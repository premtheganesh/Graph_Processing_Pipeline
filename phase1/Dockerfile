# Base image: ubuntu:22.04
FROM ubuntu:22.04

# ARGs
# https://docs.docker.com/engine/reference/builder/#understand-how-arg-and-from-interact
ARG TARGETPLATFORM=linux/amd64,linux/arm64
ARG DEBIAN_FRONTEND=noninteractive

# neo4j 5.5.0 installation and some cleanup
RUN apt-get update && \
    apt-get install -y wget gnupg software-properties-common && \
    wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add - && \
    echo 'deb https://debian.neo4j.com stable latest' > /etc/apt/sources.list.d/neo4j.list && \
    add-apt-repository universe && \
    apt-get update && \
    apt-get install -y nano unzip neo4j=1:2025.02.0 python3-pip && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#TODO: 
# Installing Python3 its dependencies and git
RUN apt-get update && \
    apt-get install -y python3 python3-pip git wget && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install pandas pyarrow neo4j && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


# Set working directory and remove files if exists
WORKDIR /cse511

RUN rm -rf /cse511

# Cloning GitHub repo directly into folder /cse511
WORKDIR /cse511
COPY data_loader.py interface.py /cse511/

# Download the required dataset
RUN wget -O yellow_tripdata_2022-03.parquet https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-03.parquet

# Configure Neo4j for external access, CSV import and allow all required GDS procedures
RUN sed -i 's/^#server\.default_listen_address=.*/server.default_listen_address=0.0.0.0/' /etc/neo4j/neo4j.conf && \
    sed -i 's/^#server\.default_advertised_address=.*/server.default_advertised_address=localhost/' /etc/neo4j/neo4j.conf && \
    sed -i 's/^#dbms\.security\.allow_csv_import_from_file_urls=.*/dbms.security.allow_csv_import_from_file_urls=true/' /etc/neo4j/neo4j.conf && \
    sed -i 's/^#dbms\.security\.procedures\.unrestricted=.*/dbms.security.procedures.unrestricted=gds.*/' /etc/neo4j/neo4j.conf && \
    sed -i 's/^#dbms\.security\.procedures\.allowlist=.*/dbms.security.procedures.allowlist=gds.*/' /etc/neo4j/neo4j.conf

# Download and install the GDS plugin (version 2.3.1)
RUN wget -O neo4j-gds.zip https://graphdatascience.ninja/neo4j-graph-data-science-2.15.0.zip && \
    unzip neo4j-gds.zip -d /var/lib/neo4j/plugins/

# Start Neo4j, wait for initialization, set the password using cypher-shell, then stop Neo4j
RUN neo4j start && \
    sleep 20 && \
    echo "ALTER CURRENT USER SET PASSWORD FROM 'neo4j' TO 'project1phase1';" | cypher-shell -u neo4j -p neo4j -d system && \
    neo4j stop


# Run the data loader script
RUN chmod +x /cse511/data_loader.py && \
    neo4j start && \
    python3 data_loader.py && \
    neo4j stop

# Expose neo4j ports
EXPOSE 7474 7687

# Start neo4j service and show the logs on container run
CMD ["/bin/bash", "-c", "neo4j start && tail -f /dev/null"]