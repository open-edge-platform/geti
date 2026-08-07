// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { type ComponentProps } from 'react';

import { Link as GetiLink } from '@geti-ui/ui';
import { openUrl } from '@tauri-apps/plugin-opener';

type LinkProps = ComponentProps<typeof GetiLink>;

export const Link = ({ href, target, onPress, ...props }: LinkProps) => {
    const shouldOpenExternally = target === '_blank' && Boolean(href);

    const handlePress: LinkProps['onPress'] = (event) => {
        onPress?.(event);

        if (shouldOpenExternally && href) {
            // Rejects when the URL is missing from the `opener:allow-open-url` allowlist in
            // src-tauri/capabilities/default.json.
            openUrl(href).catch((error) => {
                console.error('[tauri Link] failed to open url', href, error);
            });
        }
    };

    return <GetiLink {...props} href={href} target={target} onPress={handlePress} />;
};
