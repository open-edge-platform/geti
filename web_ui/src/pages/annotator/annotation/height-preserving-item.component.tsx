// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
