// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
