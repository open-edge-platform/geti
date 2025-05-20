// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Text, View } from '@geti/ui';
import { Delete } from '@geti/ui/icons';
import { isNil } from 'lodash-es';
import { useHotkeys } from 'react-hotkeys-hook';

import { KeypointNode } from '../../../../../core/annotations/shapes.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { useIsPressed } from '../../../../../hooks/use-is-pressed/use-is-pressed.hook';
import { useSelected } from '../../../../../providers/selected-provider/selected-provider.component';
import { ButtonWithSpectrumTooltip } from '../../../../../shared/components/button-with-tooltip/button-with-tooltip.component';
import { KeyMap } from '../../../../../shared/keyboard-events/keyboard.interface';
import { hasDifferentId } from '../../../../../shared/utils';
import {
    EdgeLine,
    isDifferentLabel,
    isEqualLabel,
    TemplateState,
    TemplateStateWithHistory,
    updateWithLatestPoints,
} from '../util';
import { DebouncedTextField } from './debounced-text-field.component';
import { HexadecimalColorPicker } from './hexadecimal-color-picker.component';

interface TemplateSecondaryToolbarProps {
    state: TemplateState;
    isDeleteNodeEnabled: boolean;
    onStateUpdate: (templateState: TemplateStateWithHistory) => void;
}

const getPointKey = (selectedPoint: KeypointNode, subfix: string) => {
    // By calculating the key point using the name, and position, the HexadecimalColorPicker is reset,
    // and the clamped states are updated to reflect the latest changes

    return `${selectedPoint.x}-${selectedPoint.y}-${selectedPoint.label.id}-${subfix}`;
};

const useDeleteHotkeys = <T,>(data: T | undefined, callback: (data: T) => void) => {
    useHotkeys(
        [KeyMap.Backspace, KeyMap.Delete],
        () => {
            data && callback(data);
        },
        { enabled: data !== undefined },
        [data]
    );
};

export const nodeConnectionMessage = 'Click on a node and drag the edge to another node to connect them';
export const nodeInteractionMessage = 'Click on a node to change its label color or drag it to reposition';

export const TemplateSecondaryToolbar = ({
    state,
    onStateUpdate,
    isDeleteNodeEnabled,
}: TemplateSecondaryToolbarProps) => {
    const { isSelected } = useSelected();

    const { points, edges } = state;

    const selectedEdge = state.edges.find(({ id }) => isSelected(id));
    const selectedPointIndex = points.findIndex(({ label }) => isSelected(label.id));
    const selectedPoint = points[selectedPointIndex];

    const isShiftPressed = useIsPressed({ key: KeyMap.Shift });

    const updatePoint = (label: Partial<Label>, skipHistory = false) => {
        const point = points[selectedPointIndex];
        const updatedPoints = points.with(selectedPointIndex, {
            ...point,
            label: { ...point.label, ...label },
        });

        onStateUpdate({
            edges: edges.map(updateWithLatestPoints(updatedPoints)),
            points: updatedPoints,
            skipHistory,
        });
    };

    const handleChangeLabelName = (skipHistory: boolean) => (name: string) => {
        updatePoint({ name }, skipHistory);
    };

    const handleChangeLabelColor = (color: string) => {
        updatePoint({ color });
    };

    const handleDeleteEdge = (edgeLine: EdgeLine) => {
        onStateUpdate({ points, edges: edges.filter(hasDifferentId(edgeLine.id)), skipHistory: false });
    };

    const handleDeletePoint = (point: KeypointNode) => {
        onStateUpdate({
            edges: edges.filter((currentEdge) => {
                return !isEqualLabel(currentEdge.from)(point) && !isEqualLabel(currentEdge.to)(point);
            }),
            points: points.filter(isDifferentLabel(point)),
            skipHistory: false,
        });
    };

    useDeleteHotkeys(selectedPoint, handleDeletePoint);
    useDeleteHotkeys(selectedEdge, handleDeleteEdge);

    if (isNil(selectedPoint)) {
        return (
            <Flex
                alignItems={'center'}
                gridArea={'secondaryToolbar'}
                UNSAFE_style={{
                    padding: 'var(--spectrum-global-dimension-size-100)',
                    background: 'var(--spectrum-global-color-gray-100)',
                }}
            >
                <Text>{isDeleteNodeEnabled ? nodeConnectionMessage : nodeInteractionMessage}</Text>
            </Flex>
        );
    }

    return (
        <View gridArea={'secondaryToolbar'} backgroundColor={'gray-100'} padding={'size-100'}>
            <Flex alignItems={'center'} gap={'size-125'}>
                <HexadecimalColorPicker
                    /* reset state when selected keypoint changes */
                    key={getPointKey(selectedPoint, 'color-picker')}
                    value={selectedPoint.label.color}
                    onChangeEnded={handleChangeLabelColor}
                />

                <Text>Input label</Text>

                <DebouncedTextField
                    /* reset state when selected keypoint changes */
                    key={getPointKey(selectedPoint, 'text')}
                    isRequired
                    minLength={1}
                    value={selectedPoint.label.name}
                    aria-label='label name input'
                    onChange={handleChangeLabelName(true)}
                    onChangeEnd={handleChangeLabelName(false)}
                    validationState={selectedPoint.label.name.length >= 1 ? undefined : 'invalid'}
                />
                {isDeleteNodeEnabled && (
                    <>
                        <Divider size={'S'} orientation={'vertical'} />

                        <ButtonWithSpectrumTooltip
                            isQuiet
                            isClickable
                            tooltip={`Delete point - ${selectedPoint.label.name}`}
                            isDisabled={isShiftPressed}
                            onPress={() => handleDeletePoint(selectedPoint)}
                            aria-label={`toolbar delete keypoint ${selectedPoint.label.name}`}
                        >
                            <Delete />
                        </ButtonWithSpectrumTooltip>
                    </>
                )}
            </Flex>
        </View>
    );
};
