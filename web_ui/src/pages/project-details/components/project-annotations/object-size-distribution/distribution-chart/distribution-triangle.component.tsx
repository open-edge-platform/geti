// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SVGProps } from 'react';

export const DistributionTriangle = (props: SVGProps<SVGPolygonElement>): JSX.Element => {
    return <polygon {...props} opacity={0.12} />;
};
