// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

// Fetch config json with the maintenance information
const fetchConfig = async () => {
    // TODO: Should be updated with real URL later
    const response = await fetch('https://config.app.geti.intel.com');
    const data = await response.json();

    return data;
};

// Timestamp -> human readable date
const getFormattedDate = (timestamp) => {
    // The reason for multiplying timestamp by 1000 is that the Date constructor expects the a value in MILLISECONDS
    // but we use the UNIX time, which is, by definition,
    // "the number of SECONDS that have elapsed since January 1, 1970, at 00:00:00 UTC"
    const date = new Date(timestamp * 1000);

    const options = {
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        hour12: false,
        minute: '2-digit',
        timeZone: 'UTC',
    };
    const formattedDate = date.toLocaleString('en-US', options);

    // E.g. 'November 10 at 14:16'
    return formattedDate.replace(',', ' at') + ' UTC.';
};

// Main function
const fetchMaintenanceInfo = async () => {
    try {
        const config = await fetchConfig();
        const fullDate = getFormattedDate(config.maintenance.window.end);

        const end = document.getElementById('end');
        end.innerHTML += fullDate;
    } catch (error) {
        end.innerHTML += 'soon';
    }
};

fetchMaintenanceInfo();
