// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Divider, Grid, Keyboard, Text } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import { formatHotkeyForDisplay, HOTKEYS } from '../../../../../shared/hotkeys-definition';
import { useAvailableTools } from '../../../../annotator/tools/annotator-tools/use-available-tools';

interface HotkeyItemProps {
    hotkeyName: string;
    hotkey: string;
}

const HotkeyItem = ({ hotkeyName, hotkey }: HotkeyItemProps) => {
    return (
        <>
            <Text>{hotkeyName}</Text>
            <Keyboard>{hotkey}</Keyboard>
        </>
    );
};

export const HotkeysList = () => {
    const { t } = useTranslation();
    const availableTools = useAvailableTools();

    return (
        <Grid columns={['2fr', '1fr']} rowGap={'size-100'}>
            <HotkeyItem hotkeyName={t('annotator.submitHotkeyName')} hotkey={formatHotkeyForDisplay(HOTKEYS.submit)} />
            <Divider size='S' gridColumn={'1/-1'} />
            {availableTools.map((tool) => (
                <HotkeyItem
                    key={tool.labelKey}
                    hotkeyName={t(tool.labelKey)}
                    hotkey={formatHotkeyForDisplay(tool.hotkey)}
                />
            ))}
            <Divider size='S' gridColumn={'1/-1'} />
            <HotkeyItem hotkeyName={t('annotator.undoHotkeyName')} hotkey={formatHotkeyForDisplay(HOTKEYS.undo)} />
            <HotkeyItem
                hotkeyName={t('annotator.redoHotkeyName')}
                hotkey={
                    `${formatHotkeyForDisplay(HOTKEYS.redo)} ${t('common.or')} ` +
                    `${formatHotkeyForDisplay(HOTKEYS.redoAlt)}`
                }
            />
            <HotkeyItem
                hotkeyName={t('annotator.deleteSelectedAnnotationHotkeyName')}
                hotkey={formatHotkeyForDisplay(HOTKEYS.deleteAnnotation)}
            />
            <HotkeyItem
                hotkeyName={t('annotator.toggleAnnotationsHotkeyName')}
                hotkey={formatHotkeyForDisplay(HOTKEYS.toggleAnnotationsVisibility)}
            />
            <HotkeyItem
                hotkeyName={t('annotator.selectAllAnnotationsHotkeyName')}
                hotkey={formatHotkeyForDisplay(HOTKEYS.selectAllAnnotations)}
            />
            <HotkeyItem
                hotkeyName={t('annotator.deselectAllAnnotationsHotkeyName')}
                hotkey={formatHotkeyForDisplay(HOTKEYS.deselectAllAnnotations)}
            />
            <Divider size='S' gridColumn={'1/-1'} />
            <HotkeyItem
                hotkeyName={t('annotator.resetZoomHotkeyName')}
                hotkey={formatHotkeyForDisplay(HOTKEYS.fitToScreen)}
            />
        </Grid>
    );
};
