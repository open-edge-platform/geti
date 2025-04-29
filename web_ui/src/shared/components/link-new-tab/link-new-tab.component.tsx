// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
