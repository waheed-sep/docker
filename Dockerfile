# Use ubuntu as the base image
FROM ubuntu:latest

# Set the working directory to /app
WORKDIR /app

# Install Python, Java, Maven, Git, and other dependencies
RUN apt-get update && \
    apt-get install -y python3.12 python3-pip python3.12-venv openjdk-21-jdk git maven wget curl unzip sudo && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create and activate the virtual environment and install Python packages
RUN python3.12 -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip pydriller PyYAML pandas matplotlib

# Download and unzip RefactoringMiner into /app/RefactoringMiner
RUN wget -q https://github.com/tsantalis/RefactoringMiner/releases/download/3.0.10/RefactoringMiner-3.0.10.zip && \
    unzip RefactoringMiner-3.0.10.zip -d /app && \
    mv /app/RefactoringMiner-3.0.10 /app/RefactoringMiner && \
    rm RefactoringMiner-3.0.10.zip

# Clone the jmh-xstream repository
RUN git clone --depth 1 https://github.com/waheed-sep/jmh-xstream.git /app/jmh

# Copy params.yaml and autoflow.py directly into /app
RUN curl -o /app/params.yaml https://gist.githubusercontent.com/waheed-sep/1a15212cf9844a45a3289ad0a21e660e/raw/231afa01dc440c541ca4f36fc3aab32fcf20eea0/params.yaml && \
    curl -o /app/autoflow.py https://gist.githubusercontent.com/waheed-sep/542041c5df8da143454e4e8bf4edc016/raw/145c3e6c0dc72bdf49a3ad16c1a0ad934600a124/autoflow.py

# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV MAVEN_HOME=/usr/share/maven
ENV PATH="/app/venv/bin:$JAVA_HOME/bin:$MAVEN_HOME/bin:$PATH"

# Run the Python script
CMD ["venv/bin/python", "autoflow.py"]



# # Use ubuntu as the base image
# FROM ubuntu:latest

# # Set the working directory to /app
# WORKDIR /app

# # Install Python, Java, Maven, Git, and other dependencies
# RUN apt-get update && \
#     apt-get install -y python3.12 python3-pip python3.12-venv openjdk-21-jdk git maven wget curl unzip sudo && \
#     apt-get clean && rm -rf /var/lib/apt/lists/*

# # Create and activate the virtual environment
# RUN python3.12 -m venv venv && \
#     . venv/bin/activate && \
#     pip install --upgrade pip pydriller PyYAML pandas matplotlib


# # Download and unzip RefactoringMiner into /app/RefactoringMiner
# RUN wget -q https://github.com/tsantalis/RefactoringMiner/releases/download/3.0.10/RefactoringMiner-3.0.10.zip && \
#     unzip RefactoringMiner-3.0.10.zip -d /app && \
#     mv /app/RefactoringMiner-3.0.10 /app/RefactoringMiner && \
#     rm RefactoringMiner-3.0.10.zip

# # Clone the jmh-xstream repository
# RUN git clone --depth 1 https://github.com/waheed-sep/jmh-xstream.git /tmp/repo \
#     && mkdir -p /app/jmh \
#     && cp -r /tmp/repo/* /app/jmh \
#     && rm -rf /tmp/repo

# # Copy params.yaml
# RUN curl -o /app/params.yaml https://gist.githubusercontent.com/waheed-sep/1a15212cf9844a45a3289ad0a21e660e/raw/231afa01dc440c541ca4f36fc3aab32fcf20eea0/params.yaml

# # Copy autoflow.py
# RUN curl -o /app/autoflow.py https://gist.githubusercontent.com/waheed-sep/542041c5df8da143454e4e8bf4edc016/raw/145c3e6c0dc72bdf49a3ad16c1a0ad934600a124/autoflow.py

# # Set up Python environment
# ENV PATH="/app/venv/bin:$PATH"

# # Set the correct JAVA_HOME environment variable
# ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

# # Set the PATH environment variable to include Java binaries
# ENV PATH="$JAVA_HOME/bin:$PATH"

# # Ensure the virtual environment is used in the container
# ENV PATH="/venv/bin:$PATH"

# # Set up the MAVEN_HOME environment variable
# ENV MAVEN_HOME=/usr/share/maven
# ENV PATH="$MAVEN_HOME/bin:$PATH"

# # Run the container as root to access Intel RAPL
# USER root

# # Run the Python script
# CMD ["python3", "autoflow.py"]
