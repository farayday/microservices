FROM python:3

LABEL maintainer="aliu150@bcit.ca"
# RUN mkdir /app
# We copy just the requirements.txt first to leverage Docker cache
# on `pip install`
COPY requirements.txt /app/requirements.txt
# Set the working directory
WORKDIR /app
# Install dependencies
RUN pip3 install -r requirements.txt
# Copy the source code
COPY processing/ /app
# Change permissions and become a non-privileged user
RUN mkdir -p /app/logs && mkdir -p /app/data
RUN chown -R nobody:nogroup /app
RUN chmod 755 /app/logs && chmod 755 /app/data
# Change to a non-privileged user
USER nobody
# Tells on which port the service listens in the container
EXPOSE 8100
# Entrypoint = run Python
ENTRYPOINT [ "python3" ]
# Default = run app.py
CMD [ "app.py" ]
