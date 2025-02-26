import matplotlib.pyplot as plt    # Install with: pip install matplotlib
import pandas as pd               # Install with: pip install pandas
import yaml
import csv
import os
import json

# Variables
JMH_PATH = "/app/jmh"
REPO_PATH =  "/app/repo"
RESULTS_PATH = "/app/results"
RMINER_JSON_OUTPUT = RESULTS_PATH + "/rminer_result.json"
COMMIT_JARS = RESULTS_PATH + "/commit-jars"
JMH_RESULTS = RESULTS_PATH + "/jmh-results"
PERF_DATA = RESULTS_PATH + "/perf-data"


###################################### Load <params.yaml> ######################################
def load_config(file_path='/app/params.yaml'):
    with open(file_path, 'r') as file:
        repo_params = yaml.safe_load(file)
    return repo_params

params = load_config()


# Load the CSV data
file_path = RESULTS_PATH + "/energy-perf-cmb.csv"
data = pd.read_csv(file_path)

# Sort the data by the Year column to ensure commits are ordered correctly
data = data.sort_values(by="Commit_Hash")

# Extract required columns for the plot
commits = data["Commit_Hash"]
years = data["Year"]
energy_avg = data["Energy_Avg_(uj)"]
score = data["Score"]

# Create the plot
fig, ax1 = plt.subplots(figsize=(12, 6))
fig.canvas.manager.set_window_title(params['plot']['plot_title'] + " energy consumption trend")

# Plot Energy (uJ) on the left y-axis
color = 'tab:blue'
ax1.set_xlabel("Commit (Ordered by Year)")
ax1.set_ylabel("Energy (uJ)", color=color)
ax1.plot(commits, energy_avg, marker='o', color=color, label="Energy (uJ)")
ax1.tick_params(axis='y', labelcolor=color)

# Add another y-axis for Score
ax2 = ax1.twinx()
color = 'tab:green'
ax2.set_ylabel("Performance (s/op)", color=color)
ax2.plot(commits, score, marker='o', color=color, label="Performance (s/op)")
ax2.tick_params(axis='y', labelcolor=color)

# Set the title
plt.title("Energy vs. Performance Trend " + params['plot']['plot_title'])

# Rotate x-axis labels for better readability
plt.xticks(ticks=range(len(commits)), labels=years, rotation=45, ha="right")

# Add legends for clarity
ax1.legend(loc="upper left")
ax2.legend(loc="upper right")

# Save the plot as a PNG file
plot_output_path = os.path.join(RESULTS_PATH, "plot-output.png")
plt.tight_layout()
plt.savefig(plot_output_path)

# Show the plot
plt.show()

##################################### Exporting successful commits to <summary-successful-commits.csv> ######################################

# Define the file paths
input_csv_path = RESULTS_PATH + "/commits-insights.csv"
output_csv_path = RESULTS_PATH + "/summary-successful-commits.csv"

# Read the CSV file
df = pd.read_csv(input_csv_path)

# Filter the data
filtered_df = df[(df['Status'] == 'Success') & (df['Refactorings_found'] >= 20)]

# Drop the <Status> and <Error_cause> columns
filtered_df = filtered_df.drop(columns=['Status', 'Error_cause'])

# Export the filtered data to a new CSV file
filtered_df.to_csv(output_csv_path, index=False)

print(f"Filtered data has been exported to {os.path.abspath(output_csv_path)}")

###################################### Export commits to refactorings mapping to <commit-refacts-mapping.csv>  ######################################
# Define file paths
csv_file_path = RESULTS_PATH + '/summary-successful-commits.csv'
output_csv_path = RESULTS_PATH + '/commit-refacts-mapping.csv'


# Read the commits from the CSV file
def read_commits_from_csv():
    commits = []
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header row
        for row in csv_reader:
            commits.append(row[0])  # Get the <Commit> value (first column)
    return commits


# Read the JSON file and extract the refactorings for each sha1
def read_refactorings_from_json():
    refactorings_dict = {}

    with open(RMINER_JSON_OUTPUT, mode='r', encoding='utf-8') as file:
        data = json.load(file)

        # Print the structure of the data to debug the issue
        # print("JSON Data Structure:", type(data))  # This will tell us the type of the root object
        if isinstance(data, dict):  # If the root is a dictionary
            commits_data = data.get('commits', [])  # Get the 'commits' key

            if isinstance(commits_data, list):
                current_sha1 = None
                refactorings = []

                for entry in commits_data:
                    if isinstance(entry, dict):  # Ensure each commit entry is a dictionary
                        sha1 = entry.get('sha1')
                        if sha1:
                            if current_sha1:
                                refactorings_dict[current_sha1] = refactorings
                            current_sha1 = sha1
                            refactorings = []  # Reset the refactorings list for the new sha1

                        # Add "type" values from the "refactorings" key if available
                        for refactoring in entry.get('refactorings', []):
                            if isinstance(refactoring, dict):  # Ensure refactoring is a dict
                                refactoring_type = refactoring.get('type')
                                if refactoring_type:
                                    refactorings.append(refactoring_type)

                # Don't forget the last sha1 entry
                if current_sha1:
                    refactorings_dict[current_sha1] = refactorings
            else:
                print("Error: The 'commits' key does not contain a list.")
        else:
            print("Error: JSON data is not in expected format (root should be a dictionary with 'commits' as a list).")

    return refactorings_dict


# Map commits to their refactorings types
def map_commits_to_refactorings(commits, refactorings_dict):
    commit_refactoring_mapping = []

    for commit in commits:
        refactorings = refactorings_dict.get(commit, [])
        # Fix the issue: map each commit with its refactorings
        commit_refactoring_mapping.append([commit] + refactorings)

    return commit_refactoring_mapping


# Write the results to the output CSV
def write_to_csv(commit_refactoring_mapping):
    with open(output_csv_path, mode='w', encoding='utf-8', newline='') as file:
        csv_writer = csv.writer(file, quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)  # Ensure quotes around multi-word values

        # Write headers (Commit values in first row)
        headers = [mapping[0] for mapping in commit_refactoring_mapping]  # Get commit values
        csv_writer.writerow(headers)

        # Write refactoring types in the following rows
        max_refactorings = max(len(mapping) - 1 for mapping in commit_refactoring_mapping)  # Exclude commit itself
        for i in range(max_refactorings):
            row = [mapping[i + 1] if i < len(mapping) - 1 else '' for mapping in commit_refactoring_mapping]
            csv_writer.writerow(row)


# Main execution
def main():
    commits = read_commits_from_csv()
    refactorings_dict = read_refactorings_from_json()
    commit_refactoring_mapping = map_commits_to_refactorings(commits, refactorings_dict)
    write_to_csv(commit_refactoring_mapping)


# Run the main function
if __name__ == '__main__':
    main()