// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useRef } from 'react';

import { Flex, Item, Menu, MenuTrigger, Text, View } from '@adobe/react-spectrum';
import { useUnwrapDOMRef } from '@react-spectrum/utils';
import { FocusableRefValue } from '@react-types/shared';
import { ActionButton } from '@shared/components/button/button.component';
import { Tag } from '@shared/components/tag/tag.component';
import { formatDate } from '@shared/utils';
import { usePress } from 'react-aria';

import { ChevronDownSmallLight } from '../../../../../assets/icons';
import { ModelsGroups } from '../../../../../core/models/models.interface';
import { isModelDeleted } from '../../../utils';
import { ActiveModelTag } from '../../project-models/models-container/model-card/active-model-tag.component';
import { ModelVersion } from '../../project-models/models-container/model-card/model-card.interface';
import { getVersionWithDateText } from '../utils';

import classes from '../project-model.module.scss';

interface ModelBreadcrumbProps {
    handleSelectModel: (key: Key) => void;
    selectedModel: ModelVersion;
    modelGroup: ModelsGroups;
    name: string;
}

export const ModelBreadcrumb = ({
    selectedModel,
    handleSelectModel,
    modelGroup,
    name,
}: ModelBreadcrumbProps): JSX.Element => {
    const expandButtonRef = useRef<FocusableRefValue<HTMLButtonElement>>(null);
    const selectionMenu = useUnwrapDOMRef(expandButtonRef);

    const handleOpenSelectionMenu = (): void => {
        if (selectionMenu.current == null) {
            return;
        }

        selectionMenu.current.click();
    };

    const { pressProps } = usePress({
        onPress: handleOpenSelectionMenu,
    });

    return (
        <Flex gap={'size-50'} UNSAFE_style={{ flex: '0 1 40px' }} alignItems={'center'}>
            <Text id={'algorithm-name-id'} UNSAFE_className={classes.projectModelTitle}>
                {name}
            </Text>
            <View>-</View>
            <div {...pressProps} style={{ cursor: 'pointer' }}>
                <Flex alignItems={'center'} gap={'size-150'}>
                    <View>
                        <Text id={`version-${selectedModel.version}-id`}>
                            {getVersionWithDateText(selectedModel.version, selectedModel.creationDate)}
                        </Text>
                    </View>
                    {selectedModel.isActiveModel && <ActiveModelTag id={selectedModel.id} />}

                    {isModelDeleted(selectedModel) && (
                        <Tag id={`model-archived-${selectedModel.id}`} text={'Deleted'} withDot={false} />
                    )}

                    <MenuTrigger>
                        <ActionButton
                            isQuiet
                            UNSAFE_className={classes.projectModelDropDownVersionBtn}
                            id={'expand-version-id'}
                            aria-label={'models versions list menu'}
                            ref={expandButtonRef}
                        >
                            <ChevronDownSmallLight />
                        </ActionButton>

                        <Menu onAction={handleSelectModel}>
                            {modelGroup.modelVersions.map(({ version, creationDate }) => (
                                <Item key={version} textValue={`Version: ${version}`}>
                                    {`Version: ${version} (${formatDate(creationDate, 'DD MMM YY')})`}
                                </Item>
                            ))}
                        </Menu>
                    </MenuTrigger>
                </Flex>
            </div>
        </Flex>
    );
};
