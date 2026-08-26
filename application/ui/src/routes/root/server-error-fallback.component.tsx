// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, Heading, IllustratedMessage, View } from '@geti-ui/ui';
import { CloudErrorIcon } from '@geti-ui/ui/icons';
import { useTranslation } from 'react-i18next';

import { paths } from '../../constants/paths';
import { redirectTo } from '../utils';

export const ServerErrorFallback = () => {
    const { t } = useTranslation();
    return (
        <View height={'100vh'}>
            <IllustratedMessage>
                <CloudErrorIcon size='XXL' />
                <Heading>{t('common.serverError')}</Heading>

                <Button
                    variant={'accent'}
                    marginTop={'size-200'}
                    onPress={() => {
                        redirectTo(paths.root({}));
                    }}
                >
                    {t('common.refresh')}
                </Button>
            </IllustratedMessage>
        </View>
    );
};
