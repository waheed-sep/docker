import shutil
import subprocess
import re
import json
import os
import csv
import yaml
from collections import Counter
import xml.etree.ElementTree as ET

from pydriller import Repository  # Install with: pip install pydriller
import pandas as pd               # Install with: pip install pandas
import matplotlib.pyplot as plt    # Install with: pip install matplotlib


JMH_PATH = "/app/jmh"
REPO_PATH =  "/app/repo"
RESULTS_PATH = "/app/results"
RMINER_JSON_OUTPUT = RESULTS_PATH + "/rminer_result.json"
COMMIT_JARS = RESULTS_PATH + "/commit-jars"
JMH_RESULTS = RESULTS_PATH + "/jmh-results"
PERF_DATA = RESULTS_PATH + "/perf-data"

os.makedirs(COMMIT_JARS, exist_ok=True)
os.makedirs(JMH_RESULTS, exist_ok=True)
os.makedirs(PERF_DATA, exist_ok=True)
os.makedirs(RESULTS_PATH, exist_ok=True)

MAVEN_REPO = os.path.expanduser("/root/.m2/repository")  # Maven repository path

###################################### Load <params.yaml> ######################################
def load_config(file_path='/app/params.yaml'):
    with open(file_path, 'r') as file:
        repo_params = yaml.safe_load(file)
    return repo_params

params = load_config()

###################################### Clone repository ######################################
def clone_repository(repo_url, target_directory):
    try:
        # Ensure the target directory exists
        os.makedirs(target_directory, exist_ok=True)

        # Run the git clone command
        subprocess.run(["git", "clone", repo_url, target_directory], check=True)

        print(f"Repository cloned successfully to {target_directory}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while cloning the repository: {e}")
    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")

def modify_pom_xml(pom_path, group_id, artifact_id, version):
    try:
        with open(pom_path, "r") as file:
            pom_content = file.read()

        # Replace the groupId, artifactId, and version in the pom.xml
        pom_content = pom_content.replace("<groupId>org.x-stream</groupId>", f"<groupId>{group_id}</groupId>")
        pom_content = pom_content.replace("<artifactId>xstream</artifactId>", f"<artifactId>{artifact_id}</artifactId>")
        pom_content = pom_content.replace("<version>1.4.20</version>", f"<version>{version}</version>")

        # Write the updated content back to the pom.xml
        with open(pom_path, "w") as file:
            file.write(pom_content)

        print(f"Updated {pom_path} with groupId={group_id}, artifactId={artifact_id}, version={version}")
    except Exception as ex:
        print(f"An error occurred while modifying the pom.xml file: {ex}")

def install_with_maven(project_directory):
    try:
        # Run the Maven install command
        subprocess.run(["mvn", "clean", "install", "-DskipTests"], cwd=project_directory, check=True)
        print(f"Project installed successfully to {MAVEN_REPO}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running Maven install: {e}")
    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")

if __name__ == "__main__":
    repo_url =  params['repo']['repo_url'] # "https://github.com/x-stream/xstream.git"
    clone_repository(repo_url, REPO_PATH)

    # Define your custom groupId, artifactId, and version
    group_id = params['repo']['groupId'] # "com.thoughtworks.xstream"
    artifact_id = params['repo']['artifactId'] # "xstream"
    version = params['repo']['version'] # "waheed"

    # Path to the pom.xml file in the cloned repository
    pom_path = os.path.join(REPO_PATH, "pom.xml")

    # Modify the pom.xml file
    modify_pom_xml(pom_path, group_id, artifact_id, version)

    # Install the project using Maven
    install_with_maven(REPO_PATH)

###################################### Application of RefactoringMiner ######################################
def run_refactoring_miner(repo, json_output, branch_name='master'):
    """Runs RefactoringMiner with the specified switches on a repository."""

    # Find the path for RefactoringMiner from the system's environment PATH variable
    refactoring_miner_path = "/app/RefactoringMiner/bin/RefactoringMiner"
    
    if not refactoring_miner_path:
        print("Error: RefactoringMiner not found in system PATH.")
        return

    # Construct the command for analyzing all commits in the specified branch
    command = [refactoring_miner_path, '-a', repo, branch_name, '-json', json_output]

    # # Explicitly set JAVA_HOME in the environment
    # env = os.environ.copy()
    # env['JAVA_HOME'] = "/usr/lib/jvm/java-1.21.0-openjdk-amd64"
    # env['PATH'] = f"/usr/lib/jvm/java-1.21.0-openjdk-amd64/bin:" + env['PATH']

    print("1. Running RefactoringMiner...")

    # Run the command and capture output
    # result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode == 0:
        print(f"1.1 RefactoringMiner operation successful. Results saved in {os.path.abspath(json_output)}.")
    else:
        print(f"1.1 Error running RefactoringMiner: {result.stderr.decode('utf-8')}")


# Execution
run_refactoring_miner(REPO_PATH, RMINER_JSON_OUTPUT, branch_name='master')


###################################### commits_insights ######################################

# Function to count types between sha1s and return a dictionary of counts
def count_types_between_sha1s(data):
    sha1_counts = {}
    current_sha1 = None
    type_count = 0

    def recursive_search(item):
        nonlocal current_sha1, type_count

        if isinstance(item, dict):
            for key, value in item.items():
                if key == "sha1":
                    # If a sha1 is already being counted, save it and start a new count
                    if current_sha1 is not None:
                        sha1_counts[current_sha1] = type_count

                    # Update the current sha1 and reset the type count
                    current_sha1 = value
                    type_count = 0
                elif key == "type":
                    # Increment type count if a "type" key is found
                    type_count += 1

                # Recursively search in the value
                recursive_search(value)

        elif isinstance(item, list):
            for element in item:
                # Recursively search each element in the list
                recursive_search(element)

    # Start recursive search from the root of the JSON data
    recursive_search(data)

    # If the last sha1 is found, add it to the result
    if current_sha1 is not None:
        sha1_counts[current_sha1] = type_count

    return sha1_counts


# Load the JSON data and count the refactorings
with open(RMINER_JSON_OUTPUT, 'r') as file:
    data1 = json.load(file)
    refactoring_counts = count_types_between_sha1s(data1)

# Initialize a list to store commit data
commit_data = []

# Collect commit data from the repository
for commit in Repository(REPO_PATH, only_in_branch="master").traverse_commits():
    commit_data.append({
        "Commit": commit.hash,
        "Date": commit.committer_date.date(),  # Ensure only the date part is exported
        "Files_modified": commit.files,
        "Insertions": commit.insertions,
        "Deletions": commit.deletions,
        "Refactorings_found": refactoring_counts.get(commit.hash, 0)  # Get the refactoring count or 0 if not found
    })

# Create a DataFrame from the collected data
df_commits = pd.DataFrame(commit_data)

# Sort the DataFrame by "Refactorings_found" in descending order
df_commits.sort_values(by="Refactorings_found", ascending=False, inplace=True)

# Export the DataFrame to a CSV file
df_commits.to_csv(RESULTS_PATH + '/commits-insights.csv', index=False)
print("2. Data has been exported to 'commits-insights.csv'.")


###################################### ref.type_counts ######################################

# Function to extract and count occurrences of "type" values from a JSON file
def extract_type_counts(file_path):
    # Read the JSON file content as a string
    with open(file_path, 'r') as jsonfile:
        json_content = jsonfile.read()

    # Regex pattern to find all "type" attribute values
    pattern = r'"type"\s*:\s*"([^"]+)"'
    matches = re.findall(pattern, json_content)

    # Use Counter to count occurrences of each "type" value
    type_counts_inner = Counter(matches)

    # Sort the dictionary by the values (occurrences) in descending order
    sorted_type_counts = dict(sorted(type_counts_inner.items(), key=lambda item: item[1], reverse=True))

    return sorted_type_counts


# Example usage of the type counts function
type_counts_outer = extract_type_counts(RMINER_JSON_OUTPUT)

# Convert the dictionary to a DataFrame
df_type_counts = pd.DataFrame(type_counts_outer.items(), columns=["Refactorings_found", "Occurrences"])

# Export the DataFrame to a CSV file
df_type_counts.to_csv(RESULTS_PATH + '/refs-type-counts.csv', index=False)
print("3. Data has been exported to 'refs-type-counts.csv'.")


###################################### maven build and success/failed status ######################################

# Function to update the Maven compiler options in pom.xml
def update_maven_compiler_options(pom_path):
    try:
        ET.register_namespace('', 'http://maven.apache.org/POM/4.0.0')
        tree = ET.parse(pom_path)
        root = tree.getroot()
        namespaces = {'maven': 'http://maven.apache.org/POM/4.0.0'}

        build = root.find('maven:build', namespaces)
        if build is None:
            build = ET.SubElement(root, 'build')

        plugins = build.find('maven:plugins', namespaces)
        if plugins is None:
            plugins = ET.SubElement(build, 'plugins')

        compiler_plugin = None
        for plugin in plugins.findall('maven:plugin', namespaces):
            artifact_id = plugin.find('maven:artifactId', namespaces)
            if artifact_id is not None and artifact_id.text == 'maven-compiler-plugin':
                compiler_plugin = plugin
                break

        if compiler_plugin is None:
            compiler_plugin = ET.SubElement(plugins, 'plugin')
            group_id = ET.SubElement(compiler_plugin, 'groupId')
            group_id.text = 'org.apache.maven.plugins'
            artifact_id = ET.SubElement(compiler_plugin, 'artifactId')
            artifact_id.text = 'maven-compiler-plugin'
            version = ET.SubElement(compiler_plugin, 'version')
            version.text = '3.8.1'

        configuration = compiler_plugin.find('maven:configuration', namespaces)
        if configuration is None:
            configuration = ET.SubElement(compiler_plugin, 'configuration')

        source = configuration.find('maven:source', namespaces)
        if source is None:
            source = ET.SubElement(configuration, 'source')
        source.text = '8'

        target = configuration.find('maven:target', namespaces)
        if target is None:
            target = ET.SubElement(configuration, 'target')
        target.text = '8'

        tree.write(pom_path, encoding='utf-8', xml_declaration=True)
        print(f"Updated compiler options in {pom_path} to Java 8")
    except Exception as e:
        print(f"Failed to update {pom_path}: {e}")


# Load the CSV into a DataFrame
df = pd.read_csv(RESULTS_PATH + '/commits-insights.csv')

# Ensure the "Status" and "Error_cause" columns exist
if 'Status' not in df.columns:
    df['Status'] = ""
if 'Error_cause' not in df.columns:
    df['Error_cause'] = ""

# Filter commits with 'Refactorings_found' >= 20
filtered_commits = df[df['Refactorings_found'] >= 20]['Commit'].tolist()

# Process each commit
if not filtered_commits:
    print("No commits found with 'Refactorings_found' >= 20.")
else:
    for commit_hash in filtered_commits:
        print(f"\nProcessing commit: {commit_hash}")
        os.chdir(REPO_PATH)

        # Stash any local changes, including untracked files
        try:
            subprocess.run(["git", "stash", "-u"], check=True)
            print("Local changes (including untracked files) stashed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to stash local changes: {e}")
            continue

        # Clean untracked files if any exist
        try:
            subprocess.run(["git", "clean", "-fd"], check=True)
            print("Untracked files cleaned successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to clean untracked files: {e}")
            continue

        # Checkout to the specific commit
        try:
            subprocess.run(["git", "checkout", commit_hash], check=True)
            print(f"Checked out to commit {commit_hash}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to checkout to commit {commit_hash}: {e}")
            df.loc[df['Commit'] == commit_hash, ['Status', 'Error_cause']] = ['Failed', str(e)]
            continue

        # Update pom.xml if present
        pom_path1 = os.path.join(REPO_PATH, 'pom.xml')
        if os.path.exists(pom_path1):
            update_maven_compiler_options(pom_path1)

        # Compile the project
        try:
            subprocess.run(["mvn", "clean", "package", "-Dmaven.test.skip=true", "-Drat.skip=true"], check=True)
            print(f"Project compiled successfully for commit {commit_hash}")
            df.loc[df['Commit'] == commit_hash, 'Status'] = 'Success'
        except subprocess.CalledProcessError as e:
            print(f"Failed to compile project at commit {commit_hash}: {e}")
            df.loc[df['Commit'] == commit_hash, ['Status', 'Error_cause']] = ['Failed', str(e)]

# Save the updated DataFrame back to a CSV file
df.to_csv(RESULTS_PATH + '/commits-insights.csv', index=False)
print("Builds statuses have been recorded in 'commits-insights.csv'.")

# Filter for commits with 'Refactorings_found' >= 20 and 'Success' in 'Status'
filtered_commits = df[(df['Refactorings_found'] >= 20) & (df['Status'] == 'Success')]['Commit'].tolist()

# Process each filtered commit
if not filtered_commits:
    print("5. No commits found with 'Refactorings_found' >= 20 and status 'Success'.")
else:
    for commit_hash in filtered_commits:
        print(f"\nProcessing commit: {commit_hash}")
        os.chdir(REPO_PATH)

        # Stash any local changes
        try:
            subprocess.run(["git", "stash"], check=True)
            print("5.1 Local changes stashed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"5.1 Failed to stash local changes: {e}")
            continue

        # Checkout to the specific commit
        try:
            subprocess.run(["git", "checkout", commit_hash], check=True)
            print(f"5.2 Checked out to commit {commit_hash}")
        except subprocess.CalledProcessError as e:
            print(f"5.2 Failed to checkout to commit {commit_hash}: {e}")
            continue

        # Clean previous build artifacts
        subprocess.run(["mvn", "clean"], check=True)

        # Update pom.xml if present
        pom_path1 = os.path.join(REPO_PATH, 'pom.xml')
        if os.path.exists(pom_path1):
            update_maven_compiler_options(pom_path1)

        # Compile the project
        try:
            subprocess.run(["mvn", "package", "-Dmaven.test.skip=true", "-Drat.skip=true", "-Dmaven.javadoc.skip=true"], check=True)
            print(f"5.3 Project compiled successfully for commit {commit_hash}")

            # Copy and rename only the main JAR file to avoid duplications
            target_dir = os.path.join(REPO_PATH, params['plot']['plot_title'].lower() + "/target")
            if os.path.exists(target_dir):
                jar_files = [f for f in os.listdir(target_dir) if f.endswith(".jar")]
                for jar_file in jar_files:
                    if "tests" not in jar_file and "sources" not in jar_file and "test-sources" not in jar_file:
                        old_jar_path = os.path.join(target_dir, jar_file)
                        new_jar_name = f"{commit_hash[:8]}-{jar_file}"
                        new_jar_path = os.path.join(COMMIT_JARS, new_jar_name)
                        shutil.copy2(old_jar_path, new_jar_path)
                        print(f"Copied and renamed {jar_file} to {new_jar_name}")
        except subprocess.CalledProcessError as e:
            print(f"5.3 Failed to compile project at commit {commit_hash}: {e}")

print("5.4 Process completed.\n")

###################################### Calling commits_jmh.py ######################################

# Maven install command
MAVEN_INSTALL_CMD = [
    "mvn", "install:install-file",
    "-DgroupId=" + params['repo']['groupId'],
    "-DartifactId=" + params['repo']['artifactId'],
    "-Dversion=" + params['repo']['version'],
    "-Dpackaging=jar",
    # "-DgroupId=com.thoughtworks.xstream",
    # "-DartifactId=xstream",
    # "-Dversion=waheed",
    # "-Dpackaging=jar",
]


def process_jars():
    # Get the list of JAR files in Commit-jars directory
    jar_files2 = [
        f for f in os.listdir(COMMIT_JARS)
        if f.endswith(".jar") and "javadoc" not in f.lower()
    ]

    print(f"6.1 Found {len(jar_files2)} JAR files to process (excluding 'javadoc' jars).")

    if not jar_files2:
        print("6.2 No valid JAR files found to process.")
        return

    for jar_file2 in jar_files2:
        try:
            # Extract the first 8 characters of the JAR name
            jar_name_prefix = jar_file2[:8]
            jar_path = os.path.join(COMMIT_JARS, jar_file2)

            print(f"\n6.3 Processing JAR: {jar_file2} (prefix: {jar_name_prefix})")

            # Install the JAR with Maven
            subprocess.run(MAVEN_INSTALL_CMD + [f"-Dfile={jar_path}"], check=True)
            print(f"6.4 Installed {jar_file2} successfully.")

            # Build the Uber JAR for JMH_test
            os.chdir(JMH_PATH)
            subprocess.run(["mvn", "clean", "package"], check=True)
            print("6.5 Created Uber JAR: JMH-Benchmark-MWK.jar")

            # Path to the JMH benchmark JAR
            benchmark_jar_path = os.path.join(JMH_PATH, "target", "JMH-Benchmark-MWK.jar")

            if not os.path.exists(benchmark_jar_path):
                print(f"6.5 Benchmark JAR not found: {benchmark_jar_path}")
                continue

            # Run the benchmark JAR and capture its output
            output_file = os.path.join(JMH_RESULTS, f"{jar_name_prefix}-jmh-output.txt")
            with open(output_file, "w") as output:
                # subprocess.run(["java", "--add-opens", "java.base/java.util=ALL-UNNAMED", "-jar", benchmark_jar_path, "org.openjdk.jmh.Main", "-rff", "results.json", "-rf", "json"], cwd=JMH_DIR, stdout=output, stderr=subprocess.PIPE)
                # subprocess.run(
                #     ["java", "--add-opens", "java.base/java.util=ALL-UNNAMED", "-cp",
                #      benchmark_jar_path,
                #      "org.openjdk.jmh.Main", "-rff", f"{PERF_DATA}/{jar_name_prefix}-perf-data.json", "-rf", "json"
                #      ],
                #     cwd=JMH_PATH,
                #     stdout=output,
                #     stderr=subprocess.PIPE)
                subprocess.run(
                    ["java", 
                    "--add-opens", "java.base/java.util=ALL-UNNAMED", 
                    "--add-opens", "java.base/java.lang.reflect=ALL-UNNAMED",
                    "--add-opens", "java.base/java.text=ALL-UNNAMED",
                    "--add-opens", "java.desktop/java.awt.font=ALL-UNNAMED",
                    "-cp", benchmark_jar_path, 
                    "org.openjdk.jmh.Main", 
                    "-rff", f"{PERF_DATA}/{jar_name_prefix}-perf-data.json", 
                    "-rf", "json"
                    ],
                    cwd=JMH_PATH,
                    stdout=output,
                    stderr=subprocess.PIPE
                )
                
                print(f"6.6 Saved benchmark output to {os.path.abspath(output_file)}")

                # Rename and move the generated res.csv file
                # result_csv = os.path.join(RESULTS_OUTPUT, "result.csv")
                # if os.path.exists(result_csv):
                #     summary_csv = os.path.join(JMH_RESULTS, f"{jar_name_prefix}-summary.csv")
                #     shutil.move(result_csv, summary_csv)
                #     print(f"6.7 Saved CSV to {summary_csv}")
                # else:
                #     print(f"6.7 No result.csv file found for JAR: {jar_file2}")

        except subprocess.CalledProcessError as e:
            print(f"Error processing {os.path.abspath(jar_file2)}: {e}")
        except Exception as e:
            print(f"Unexpected error for {os.path.abspath(jar_file2)}: {e}")

    print("\nProcessing completed.")


if __name__ == "__main__":
    process_jars()


##################################### Energy computation ######################################
def process_files_with_commit_insights(directory_path, commits_csv_path, output_csv_path):
    try:
        # Check if directory exists
        if not os.path.exists(directory_path):
            print(f"Error: The directory '{os.path.abspath(directory_path)}' does not exist.")
            return

        if not os.path.exists(commits_csv_path):
            print(f"Error: The file '{os.path.abspath(commits_csv_path)}' does not exist.")
            return

        results = []

        # Read commits insights file into a dictionary for faster lookups
        commits_data = {}
        with open(commits_csv_path, 'r') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)  # Skip the header row
            for row in reader:
                if len(row) >= 2:
                    hash_value = row[0][:8]  # Use only the first 8 characters of the hash
                    date = row[1]
                    year = date.split('-')[0]  # Extract the year part from the DATE (format: YYYY-MM-DD)
                    commits_data[hash_value] = year

        # Iterate through all files in the directory
        for file_name in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file_name)

            # Only process files (skip directories)
            if os.path.isfile(file_path):
                file_hash = file_name[:8]  # Get the first 8 characters of the file name

                try:
                    with open(file_path, 'r') as file:
                        lines = file.readlines()

                    # Initialize variables for sum and count
                    total_sum = 0
                    count = 0

                    # Define the pattern to match numbers ending with '+' and exclude " 0+"
                    pattern = re.compile(r'(\d+)\+')

                    # Process each line in the file
                    for line in lines:
                        line = line.strip()  # Remove leading/trailing whitespace

                        # Skip lines starting with "#"
                        if line.startswith("#"):
                            continue

                        matches = pattern.findall(line)
                        for match in matches:
                            # Exclude matches that are explicitly "0"
                            if match == "0":
                                continue

                            total_sum += int(match)  # Convert to integer and add to sum
                            count += 1

                    # Calculate average if numbers were found
                    if count > 0:
                        average = total_sum / count
                    else:
                        average = None

                    # Find the matching year from the commits data
                    year = commits_data.get(file_hash, "Unknown")

                    # Append results as a tuple
                    if average is not None:
                        results.append([file_hash, f"{average:.2f}", count, year])

                except Exception as e:
                    print(f"Error processing file '{os.path.abspath(file_name)}': {str(e)}")

        # Write results to the output CSV
        with open(output_csv_path, 'w', newline='') as output_file:
            writer = csv.writer(output_file)
            writer.writerow(["HASH", "AVERAGE", "TOTAL_NUMBERS", "YEAR"])  # Write the header row
            writer.writerows(results)  # Write the data rows

        print(f"Results saved to {output_csv_path}.")

    except Exception as e:
        print(f"Error: {str(e)}")


# Define paths
input_directory = os.path.join(RESULTS_PATH, "jmh-results")
commits_csv = os.path.join(RESULTS_PATH, "commits-insights.csv")
output_csv = os.path.join(RESULTS_PATH, "energy-data.csv")

# Process files and save results
process_files_with_commit_insights(input_directory, commits_csv, output_csv)

###################################### Performance computation  ######################################
# Define file paths
json_dir = os.path.join(RESULTS_PATH, "perf-data")
csv_file = os.path.join(RESULTS_PATH, "commits-insights.csv")
output_file = os.path.join(json_dir, "perf-data.csv")


# Function to extract the year from "Commits insights.csv"
def get_year_mapping(csv_file):
    hash_year_map = {}
    try:
        with open(csv_file, mode="r") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row if any
            for row in reader:
                if len(row) >= 2:  # Ensure there are at least two columns
                    commit_hash = row[0][:8]
                    commit_date = row[1]
                    year = commit_date.split("-")[0] if "-" in commit_date else ""
                    hash_year_map[commit_hash] = year
    except Exception as e:
        print(f"Error reading '{os.path.abspath(csv_file)}': {e}")
    return hash_year_map


# Function to process JSON files and extract scores
def process_json_files(json_dir, hash_year_map):
    results = []
    for file_name in os.listdir(json_dir):
        if file_name.endswith(".json"):
            json_path = os.path.join(json_dir, file_name)
            try:
                with open(json_path, mode="r") as file:
                    data = json.load(file)  # Load JSON data
                    if isinstance(data, list):  # Check if the top-level object is a list
                        scores = [
                            entry["primaryMetric"]["score"]
                            for entry in data
                            if "primaryMetric" in entry and "score" in entry["primaryMetric"]
                        ]

                        if len(scores) > 1:
                            second_score = scores[1]
                            commit_hash = file_name[:8]
                            year = hash_year_map.get(commit_hash, "Unknown")
                            results.append((commit_hash, second_score, year))
            except Exception as e:
                print(f"Error processing '{os.path.abspath(json_path)}': {e}")
    return results


# Write results to CSV
def write_to_csv(results, output_file):
    try:
        with open(output_file, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Commit_Hash", "Score", "Year"])
            writer.writerows(results)
        print(f"Results written to '{os.path.abspath(output_file)}'")
    except Exception as e:
        print(f"Error writing to '{output_file}': {e}")


# Main workflow
if __name__ == "__main__":
    hash_year_map = get_year_mapping(csv_file)
    results = process_json_files(json_dir, hash_year_map)
    write_to_csv(results, output_file)

###################################### Energy and Performance combined score ######################################
# File paths
plot_data_file = RESULTS_PATH + "/energy-data.csv"
perf_data_file = RESULTS_PATH + "/perf-data/perf-data.csv"
output_file = RESULTS_PATH + "/energy-perf-cmb.csv"

# Read plot_data.csv
average_data = {}
with open(plot_data_file, mode="r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        hash_value = row.get("HASH")
        average = row.get("AVERAGE")
        if hash_value and average:
            average_data[hash_value.strip()] = average.strip()

# Update perf-data.csv
with open(perf_data_file, mode="r") as infile, open(output_file, mode="w", newline="") as outfile:
    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames + ["Energy_Avg_(uj)"]  # Add new field for performance
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)

    # Write headers
    writer.writeheader()

    # Write rows with added Performance column
    for row in reader:
        commit_hash = row.get("Commit_Hash").strip()
        row["Energy_Avg_(uj)"] = average_data.get(commit_hash, "")  # Match and add Average value
        writer.writerow(row)

print(f"Updated file created at: {output_file}")