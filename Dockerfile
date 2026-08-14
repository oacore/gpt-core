FROM python:3.12-slim


# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

COPY . .
# Install dependencies from Pipfile
# Use --system to install packages directly to the system Python instead of creating a virtualenv
RUN pipenv install --system --deploy --ignore-pipfile

# Copy your application code
# Run the Python command directly

CMD python main.py