#!/bin/bash
sudo apt update
sudo apt install -y apache2
curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/index" -H "Metadata-Flavor:Google" | sudo tee /var/www/html/index.html > /dev/null
