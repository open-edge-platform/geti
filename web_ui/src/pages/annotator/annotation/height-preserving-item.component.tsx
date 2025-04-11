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

import { CSSProperties, useEffect, useState } from 'react';

import { ItemProps } from 'react-virtuoso';

import classes from './height-preserving-item.module.scss';

export const HeightPreservingItem = ({ children, ...props }: ItemProps<unknown>) => {
    const [size, setSize] = useState(0);
    const knownSize = props['data-known-size'];

    useEffect(() => {
        setSize((prevSize) => (knownSize == 0 ? prevSize : knownSize));
    }, [knownSize]);

    return (
        <div
            {...props}
            className={classes.container}
            // check styling in the style tag below
            style={{ '--child-height': `${size}px` } as CSSProperties}
        >
            {children}
        </div>
    );
};
