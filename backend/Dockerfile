ARG PLATFORM=x86_64

FROM --platform=${PLATFORM} public.ecr.aws/lambda/python:3.11

# Copy poetry files
COPY pyproject.toml poetry.lock ${LAMBDA_TASK_ROOT}/

# Install poetry and dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "lambda_handler.handler" ] 
