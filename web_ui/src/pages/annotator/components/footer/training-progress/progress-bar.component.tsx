// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
