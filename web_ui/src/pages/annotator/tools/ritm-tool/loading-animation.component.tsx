// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.
// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

export const LoadingAnimation = ({ x, y, radius }: { x: number; y: number; radius: number }): JSX.Element => {
    return (
        <g transform={`translate(${x} ${y}) scale(${radius}, ${radius})`}>
            <path d='M 0 -25 A 25 25 00 0 1 0 25' stroke='black' strokeWidth='4' fillOpacity='0'>
                <animateTransform
                    attributeName='transform'
                    attributeType='XML'
                    type='rotate'
                    dur='1s'
                    from='0 0 0'
                    to='360 0 0'
                    repeatCount='indefinite'
                />
            </path>
        </g>
    );
};
