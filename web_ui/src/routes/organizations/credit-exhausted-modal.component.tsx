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

import {
    ButtonGroup,
    Content,
    Dialog,
    DialogContainer,
    Divider,
    Heading,
    Text,
    useNumberFormatter,
} from '@adobe/react-spectrum';

import { CONTACT_SUPPORT } from '../../core/const';
import { useCreditsQueries } from '../../core/credits/hooks/use-credits-api.hook';
import { GLOBAL_MODALS_KEYS } from '../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../core/user-settings/hooks/use-global-settings.hook';
import { getSettingsOfType } from '../../core/user-settings/utils';
import { Button } from '../../shared/components/button/button.component';
import { isBalanceLow } from '../../shared/components/header/credit-balance/util';
import { ONE_MINUTE, openNewTab } from '../../shared/utils';

interface CreditExhaustedModalProps {
    organizationId: string;
}

export const CreditExhaustedModal = ({ organizationId }: CreditExhaustedModalProps) => {
    const settings = useUserGlobalSettings();
    const numberFormatter = useNumberFormatter({});
    const { useGetOrganizationBalanceQuery } = useCreditsQueries();

    const globalModalsConfig = getSettingsOfType(settings.config, GLOBAL_MODALS_KEYS);

    const isWelcomeModalDisabled = globalModalsConfig[GLOBAL_MODALS_KEYS.WELCOME_MODAL].isEnabled === false;
    const isExhaustedModalEnabled =
        globalModalsConfig[GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL].isEnabled;
    const isLowCreditsModalEnabled = globalModalsConfig[GLOBAL_MODALS_KEYS.LOW_ORGANIZATION_CREDITS_MODAL].isEnabled;

    const { data: organizationBalance, isLoading } = useGetOrganizationBalanceQuery(
        { organizationId },
        { refetchInterval: ONE_MINUTE }
    );

    const closeModal = (key: GLOBAL_MODALS_KEYS) => {
        settings.saveConfig({
            ...settings.config,
            [key]: { isEnabled: false },
        });
    };

    if (!organizationBalance || isLoading) {
        return <></>;
    }

    const isOpenLowOrgCreditsModal =
        isWelcomeModalDisabled && isLowCreditsModalEnabled && isBalanceLow(organizationBalance);
    const isOpenExhaustedOrgCreditsModal =
        isWelcomeModalDisabled && isExhaustedModalEnabled && organizationBalance.available === 0;
    const isOpen = isOpenLowOrgCreditsModal || isOpenExhaustedOrgCreditsModal;
    const modalKey = isOpenExhaustedOrgCreditsModal
        ? GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL
        : GLOBAL_MODALS_KEYS.LOW_ORGANIZATION_CREDITS_MODAL;

    return (
        <DialogContainer type={'modal'} onDismiss={() => closeModal(modalKey)}>
            {isOpen && (
                <Dialog maxWidth={'74rem'}>
                    <Heading>Credits {isOpenExhaustedOrgCreditsModal ? 'have been exhausted' : 'are low'}</Heading>

                    <Divider />

                    <Content>
                        <Text>
                            You have spent {isOpenExhaustedOrgCreditsModal ? '' : 'almost '} all{' '}
                            {numberFormatter.format(organizationBalance.incoming)} available credits. Your operations
                            such as model training
                            {isOpenExhaustedOrgCreditsModal ? ' are not available' : ' can soon become unavailable'}.
                        </Text>

                        <Divider size={'S'} marginTop={'size-150'} />
                    </Content>

                    <ButtonGroup>
                        <Button
                            variant={'primary'}
                            onPress={() => closeModal(modalKey)}
                            id={'close-credit-exhausted'}
                            aria-label={'close credit exhausted'}
                        >
                            Close
                        </Button>
                        <Button
                            variant={'accent'}
                            onPress={() => {
                                closeModal(modalKey);
                                openNewTab(CONTACT_SUPPORT);
                            }}
                        >
                            Contact support
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
