#!/bin/bash

LOG_FILE="/Users/moornmo/Dev/odoo/generate.log"

# Clear previous log content
> $LOG_FILE

echo "--- Starting Odoo Module Update and Dummy Data Generation ---" >> $LOG_FILE
echo "Log file: $LOG_FILE" >> $LOG_FILE
echo "Timestamp: $(date)" >> $LOG_FILE
echo "-------------------------------------------------------------" >> $LOG_FILE

# Install/Update iload module
echo "Step 1: Installing/Updating iload module..." >> $LOG_FILE
/Users/moornmo/Dev/odoo/odoo-bin -d iload -u iload --addons-path=/Users/moornmo/Dev/odoo/odoo/addons,/Users/moornmo/Dev/odoo/addons,/Users/moornmo/Dev/odoo/custom_addons >> $LOG_FILE 2>&1

# Run dummy data generation script
echo "Step 2: Running dummy data generation script..." >> $LOG_FILE
/Users/moornmo/Dev/odoo/odoo-bin shell -d iload --addons-path=/Users/moornmo/Dev/odoo/odoo/addons,/Users/moornmo/Dev/odoo/addons,/Users/moornmo/Dev/odoo/custom_addons < /Users/moornmo/Dev/odoo/generate_dummy_data.py >> $LOG_FILE 2>&1

echo "-------------------------------------------------------------" >> $LOG_FILE
echo "--- Odoo Module Update and Dummy Data Generation Complete ---" >> $LOG_FILE
echo "Timestamp: $(date)" >> $LOG_FILE
