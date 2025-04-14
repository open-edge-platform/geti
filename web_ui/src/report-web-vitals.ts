// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

type ReportHandler = <T>(metric: T) => void;

const reportWebVitals = (reportHandler?: ReportHandler): void => {
    if (reportHandler === undefined) {
        return;
    }

    import('web-vitals').then(({ onLCP, onINP, onCLS, onFID, onTTFB }) => {
        onLCP(reportHandler);
        onINP(reportHandler);
        onCLS(reportHandler);
        onFID(reportHandler);
        onTTFB(reportHandler);
    });
};

export default reportWebVitals;
