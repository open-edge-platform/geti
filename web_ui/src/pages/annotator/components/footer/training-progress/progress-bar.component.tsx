// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

type ProgressBarProps = {
    completed: number;
    width: string | undefined;
    progressBarColor: string;
    backgroundColor: string;
};

export const ProgressBar: React.FC<ProgressBarProps> = ({ width, completed, progressBarColor, backgroundColor }) => {
    const filledWidth = `${Math.min(Number(completed), 100)}%`;
    const filledStyle = {
        height: '100%',
        width: filledWidth,
        background: progressBarColor,
        transition: `width 1s ease-in-out`,
        borderRadius: 'inherit',
    };

    return (
        <div
            style={{ display: 'initial' }}
            role='progressbar'
            aria-valuenow={completed}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuetext={`${completed}%`}
        >
            <div style={{ height: '100%', width, backgroundColor, overflow: 'hidden' }}>
                <div style={filledStyle} />
            </div>
        </div>
    );
};
