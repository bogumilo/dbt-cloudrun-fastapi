# dbt Python image
FROM ghcr.io/dbt-labs/dbt-bigquery:1.5.6

# Set the working directory to /app
WORKDIR /app

# copy the requirements file used for dependencies
COPY requirements.txt .

# Install pip packages from .txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

COPY . .

# Install dbt dependencies
RUN dbt deps --profiles-dir dbt_project --project-dir dbt_project

# Run app
ENTRYPOINT ["python", "app.py"]
