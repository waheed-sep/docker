import webbrowser
import csv

# Variables
JMH_PATH = "/app/jmh"
REPO_PATH =  "/app/repo"
RESULTS_PATH = "/app/results"
RMINER_JSON_OUTPUT = RESULTS_PATH + "/rminer_result.json"
COMMIT_JARS = RESULTS_PATH + "/commit-jars"
JMH_RESULTS = RESULTS_PATH + "/jmh-results"
PERF_DATA = RESULTS_PATH + "/perf-data"


# Define paths
success_commits = RESULTS_PATH + "/summary-successful-commits.csv"
refacts_mapping = RESULTS_PATH + "/commit-refacts-mapping.csv"
energy_data_file = RESULTS_PATH + "/energy-data.csv"
perf_data_file = RESULTS_PATH + "/perf-data/perf-data.csv"
energy_perf_file = RESULTS_PATH + "/energy-perf-cmb.csv"
image_file = RESULTS_PATH + "/plot-output.png"
html_file = RESULTS_PATH + "/results-summary.html"

# Function to read CSV data and add row numbers
def read_csv_with_row_numbers(csv_file):
    table_data = []
    try:
        with open(csv_file, mode="r") as file:
            csv_reader = csv.reader(file)
            table_data = list(csv_reader)
        # Add row numbers to the table data
        for i, row in enumerate(table_data):
            if i == 0:
                row.insert(0, "No.")  # Add "No." as the header for the row number column
            else:
                row.insert(0, str(i))  # Add row numbers starting from 1
    except FileNotFoundError:
        print(f"Error: {csv_file} not found.")
        exit(1)
    return table_data

# Read data from all CSV files
success_commit_table = read_csv_with_row_numbers(success_commits)
refacts_mapping_table = read_csv_with_row_numbers(refacts_mapping)
energy_data = read_csv_with_row_numbers(energy_data_file)
perf_data = read_csv_with_row_numbers(perf_data_file)
energy_perf_data = read_csv_with_row_numbers(energy_perf_file)

# Generate HTML content
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Results Summary</title>
    <style>
        body {{
            font-family: Arial, sans-serif, Lucida Console;
            margin: 0;
            padding: 0;
        }}
        h1, h2, p {{
            text-align: center; /* Center-align all headings and paragraphs */
            color: #990099
        }}
        h1 {{
            margin-bottom: 20px;
            color: black
        }}
        .nav-buttons {{
            text-align: center;
            margin: 20px 0;
            position: sticky;
            top: 0;
            background: white;
            z-index: 1000;
            padding: 10px 0;
        }}
        .nav-buttons button {{
            margin: 0 10px;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
        }}
        .page {{
            display: none; /* Hide all pages by default */
            padding: 20px;
        }}
        #home {{
            display: flex; /* Show Home page by default */
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 80vh; /* Center content vertically */
        }}
        .table-container {{
            width: 100%;
            overflow-x: auto;
            margin: 20px 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        th, td {{
            border: 1px solid black;
            padding: 8px;
            text-align: center;
        }}
        th {{
            font-weight: bold;
            color: #990099
        }}
        img {{
            display: block;
            margin: 20px auto;
            max-width: 80%;
            height: auto;
        }}
        .highlight {{
            color: #990099;
        }}
    </style>
</head>
<body>
    <h1>ENTRAN: <span class="highlight">EN</span>ergy <span class="highlight">TR</span>end <span class="highlight">AN</span>alysis on OSS Java libraries</h1>

    <!-- Navigation Buttons -->
    <div class="nav-buttons">
        <button onclick="showPage('home')">Home</button>
        <button onclick="showPage('summary-table')">Summary</button>
        <button onclick="showPage('refactoring-table')">Mapping</button>
        <button onclick="showPage('energy-data')">Energy Data</button>
        <button onclick="showPage('performance-data')">Performance Data</button>
        <button onclick="showPage('energy-performance-data')">Energy + Performance</button>
        <button onclick="showPage('plot-image')">Plot</button>
    </div>

    <!-- Home Page -->
    <div id="home" class="page">
        <h2>Welcome to the Entran Results Summary</h2>
        <p>Click on the buttons above to view the summary table, refactoring table, energy data, performance data, combined energy and performance data, or plot.</p>
    </div>

    <!-- Summary Successful Commits Table -->
    <div id="summary-table" class="page">
        <h2>Summary Successful Commits</h2>
        <div class="table-container">
            <table>
                <tr>
                    {"".join(f"<th><strong>{cell}</strong></th>" for cell in success_commit_table[0])}
                </tr>
                {"".join(f"<tr>{''.join(f'<td>{cell}</td>' for cell in row)}</tr>" for row in success_commit_table[1:])}
            </table>
        </div>
    </div>

    <!-- Commit Refactoring Mapping Table -->
    <div id="refactoring-table" class="page">
        <h2>Commit Refactoring Mapping</h2>
        <div class="table-container">
            <table>
                <tr>
                    {"".join(f"<th><strong>{cell}</strong></th>" for cell in refacts_mapping_table[0])}
                </tr>
                {"".join(f"<tr>{''.join(f'<td>{cell}</td>' for cell in row)}</tr>" for row in refacts_mapping_table[1:])}
            </table>
        </div>
    </div>

    <!-- Energy Data Table -->
    <div id="energy-data" class="page">
        <h2>Energy Data</h2>
        <div class="table-container">
            <table>
                <tr>
                    {"".join(f"<th><strong>{cell}</strong></th>" for cell in energy_data[0])}
                </tr>
                {"".join(f"<tr>{''.join(f'<td>{cell}</td>' for cell in row)}</tr>" for row in energy_data[1:])}
            </table>
        </div>
    </div>

    <!-- Performance Data Table -->
    <div id="performance-data" class="page">
        <h2>Performance Data</h2>
        <div class="table-container">
            <table>
                <tr>
                    {"".join(f"<th><strong>{cell}</strong></th>" for cell in perf_data[0])}
                </tr>
                {"".join(f"<tr>{''.join(f'<td>{cell}</td>' for cell in row)}</tr>" for row in perf_data[1:])}
            </table>
        </div>
    </div>

    <!-- Energy + Performance Data Table -->
    <div id="energy-performance-data" class="page">
        <h2>Energy + Performance Data</h2>
        <div class="table-container">
            <table>
                <tr>
                    {"".join(f"<th><strong>{cell}</strong></th>" for cell in energy_perf_data[0])}
                </tr>
                {"".join(f"<tr>{''.join(f'<td>{cell}</td>' for cell in row)}</tr>" for row in energy_perf_data[1:])}
            </table>
        </div>
    </div>

    <!-- Plot Image -->
    <div id="plot-image" class="page">
        <h2>Plot Output</h2>
        <img src="plot-output.png" alt="Plot Output">
    </div>

    <script>
        // Function to show a specific page and hide others
        function showPage(pageId) {{
            // Hide all pages
            document.querySelectorAll('.page').forEach(page => {{
                page.style.display = 'none';
            }});
            // Show the selected page
            document.getElementById(pageId).style.display = 'block';
        }}

        // Show Home page by default
        showPage('home');
    </script>
</body>
</html>
"""

# Write the HTML content to the file
try:
    with open(html_file, "w") as file:
        file.write(html_content)
    print(f"{html_file} has been created successfully.")
except Exception as e:
    print(f"Error writing to {html_file}: {e}")
    exit(1)

# Open the HTML file in the default web browser
try:
    webbrowser.open(f"file://{html_file}")
    print(f"Opening {html_file} in the default web browser...")
except Exception as e:
    print(f"Error opening {html_file} in the browser: {e}")