// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties } from 'react';

import { Button, ButtonGroup, Flex, Heading, Item, Menu, MenuTrigger, Text, View } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import { MoreMenu } from '../../../assets/icons';
import { TUTORIAL_CARD_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { useDocsUrl } from '../../../hooks/use-docs-url/use-docs-url.hook';
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
