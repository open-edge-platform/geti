// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Link } from 'react-router-dom';

interface LinkNewTabProps {
    text: string;
    url: string;
    className?: string;
    ariaLabel?: string;
}

export const LinkNewTab = ({ text, url, className, ariaLabel }: LinkNewTabProps): JSX.Element => {
    return (
        <Link
            aria-label={ariaLabel}
            className={className}
            to={url}
            style={{ color: 'var(--energy-blue)', textDecoration: 'none' }}
            target={'_blank'}
            rel={'noopener noreferrer'}
        >
            {text}
        </Link>
    );
};
