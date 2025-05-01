// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { Item, Menu, MenuTrigger, Selection, Text } from '@adobe/react-spectrum';
import { ActionButton } from '@shared/components/button/button.component';

import { ChevronDownSmall } from '../../../../assets/icons';
import { AnnotationSceneState, SearchRuleValue } from '../../../../core/media/media-filter.interface';
import { ANNOTATION_SCENE_OPTIONS, getAnnotationSceneStatesFromText } from '../../utils';

import classes from '../../media-filter.module.scss';

interface MediaFilterValueAnnotationSceneStateProps {
    value: string | string[];
    isAnomalyProject: boolean;
    isTaskChainProject: boolean;
    onSelectionChange: (key: SearchRuleValue) => void;
    isMultiselection?: boolean;
}

export const anomalyItems = [AnnotationSceneState.ANNOTATED, AnnotationSceneState.PARTIALLY_ANNOTATED];

export const MediaFilterValueAnnotationSceneState = ({
    value,
    isAnomalyProject,
    isTaskChainProject,
    onSelectionChange,
    isMultiselection = false,
}: MediaFilterValueAnnotationSceneStateProps): JSX.Element => {
    const options = useMemo(() => {
        if (isAnomalyProject) {
            return ANNOTATION_SCENE_OPTIONS.filter(({ key }) => anomalyItems.includes(key));
        } else if (!isTaskChainProject) {
            return ANNOTATION_SCENE_OPTIONS.filter(({ key }) => key !== AnnotationSceneState.PARTIALLY_ANNOTATED);
        } else {
            return ANNOTATION_SCENE_OPTIONS;
        }
    }, [isAnomalyProject, isTaskChainProject]);

    const selectedAnnotationSceneStates = getAnnotationSceneStatesFromText(value === '' ? [] : value);
    const selectedKeys = selectedAnnotationSceneStates.map(({ key }) => key);
    const displayText =
        selectedAnnotationSceneStates.length > 0
            ? selectedAnnotationSceneStates.map(({ text }) => text).join(', ')
            : 'Select an Option';

    const handleOnChange = (selection: Selection) => {
        if (selection === 'all') {
            return;
        }
        const selected = options.filter((option) => selection.has(option.key));

        onSelectionChange(isMultiselection ? selected.map((option) => option.key) : selected[0].key);
    };

    return (
        <MenuTrigger>
            <ActionButton
                isQuiet
                id='media-filter-annotation-scene-state'
                aria-label='media-filter-annotation-scene-state'
                UNSAFE_className={[
                    classes.mediaPicker,
                    selectedAnnotationSceneStates.length === 0 && classes.placeHolder,
                ].join(' ')}
            >
                <Text>{displayText}</Text>
                <ChevronDownSmall width={22} height={22} />
            </ActionButton>
            <Menu
                items={options}
                selectionMode={isMultiselection ? 'multiple' : 'single'}
                selectedKeys={selectedKeys}
                onSelectionChange={handleOnChange}
            >
                {({ key, text }) => (
                    <Item textValue={text} key={key} aria-label={key.toLocaleLowerCase()}>
                        <Text>{text}</Text>
                    </Item>
                )}
            </Menu>
        </MenuTrigger>
    );
};
