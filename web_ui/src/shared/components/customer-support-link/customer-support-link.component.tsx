// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Link } from '@geti/ui';
import { clsx } from 'clsx';

import { CONTACT_SUPPORT } from '../../../core/const';

import classes from './customer-support-link.module.scss';

interface ContactSupportLinkProps {
    className?: string;
    text?: string;
}

export const CustomerSupportLink = ({ className, text = 'customer support' }: ContactSupportLinkProps): JSX.Element => {
    return (
        <Link UNSAFE_className={clsx(classes.link, className)}>
            <a target={'_blank'} rel='noopener noreferrer' href={CONTACT_SUPPORT}>
                {text}
            </a>
        </Link>
    );
};
