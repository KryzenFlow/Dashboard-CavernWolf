FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends iptables \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY run_agent.sh /app/run_agent.sh
RUN chmod +x /app/run_agent.sh

# No secrets baked into the image
CMD ["/app/run_agent.sh"]
