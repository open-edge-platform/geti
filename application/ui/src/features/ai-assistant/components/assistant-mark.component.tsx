// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { SVGProps } from 'react';

import type { AiVendor } from '../types';

export const ChatGptMark = (props: SVGProps<SVGSVGElement>) => (
    <svg viewBox='0 0 24 24' aria-hidden='true' {...props}>
        <circle cx='12' cy='12' r='9' fill='none' stroke='currentColor' strokeWidth='2' />
        <path d='M8 9.5h8M8 14.5h5' fill='none' stroke='currentColor' strokeLinecap='round' strokeWidth='2' />
    </svg>
);

export const ClaudeMark = (props: SVGProps<SVGSVGElement>) => (
    <svg viewBox='0 0 24 24' aria-hidden='true' {...props}>
        <path
            d='M12 3v18M3 12h18M5.6 5.6l12.8 12.8M18.4 5.6 5.6 18.4'
            fill='none'
            stroke='currentColor'
            strokeLinecap='round'
            strokeWidth='2.2'
        />
    </svg>
);

export const markForVendor = (vendor: AiVendor) => (vendor === 'openai' ? ChatGptMark : ClaudeMark);
