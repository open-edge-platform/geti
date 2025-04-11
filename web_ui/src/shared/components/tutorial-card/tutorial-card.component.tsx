// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { CSSProperties } from 'react';

import { ButtonGroup, Flex, Heading, Item, Menu, MenuTrigger, Text, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { MoreMenu } from '../../../assets/icons';
import { TUTORIAL_CARD_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { useDocsUrl } from '../../../hooks/use-docs-url/use-docs-url.hook';
import { Button } from '../button/button.component';
import { QuietActionButton } from '../quiet-button/quiet-action-button.component';
import { onPressLearnMore } from '../tutorials/utils';
import { getCardData } from './utils';

import classes from './tutorial-card.module.scss';

interface TutorialCardProps {
    id: TUTORIAL_CARD_KEYS;
    isLoading: boolean;
    onPressDismiss: () => void;
    onPressDismissAll: () => void;
    styles?: CSSProperties;
}

export const TutorialCard = ({
    id,
    styles,
    isLoading,
    onPressDismiss,
    onPressDismissAll,
}: TutorialCardProps): JSX.Element => {
    const { header, description, docUrl } = getCardData(id);
    const url = useDocsUrl();
    const newDocUrl = `${url}${docUrl}`;

    if (isEmpty(description)) {
        return <></>;
    }

    return (
        <View UNSAFE_className={classes.dialogWrapper} UNSAFE_style={styles}>
            {header && <Heading UNSAFE_className={classes.tutorialCardHeader}>{header}</Heading>}
            <Text UNSAFE_className={classes.dialogDescription}>{description}</Text>
            <ButtonGroup UNSAFE_className={classes.dialogButtonGroup}>
                <Flex>
                    {docUrl && (
                        <Button
                            variant='primary'
                            id={`${id}-learn-more-button-id`}
                            onPress={() => {
                                onPressLearnMore(newDocUrl);
                            }}
                        >
                            Learn more
                        </Button>
                    )}
                    <Button variant='primary' id='dismiss-button-id' isPending={isLoading} onPress={onPressDismiss}>
                        Dismiss
                    </Button>
                </Flex>

                <MenuTrigger>
                    <QuietActionButton
                        id={`${id}-more-btn-id`}
                        aria-label='Open to dismiss all help dialogs'
                        data-testid={`${id}-more-btn-id`}
                        UNSAFE_className={classes.moreMenu}
                    >
                        <MoreMenu />
                    </QuietActionButton>
                    <Menu id={`${id}-tutorial-card-menu-id`} onAction={onPressDismissAll}>
                        <Item key={id} test-id={`${id}-dismiss-all-id`} textValue='Dismiss all'>
                            Dismiss all
                        </Item>
                    </Menu>
                </MenuTrigger>
            </ButtonGroup>
        </View>
    );
};
