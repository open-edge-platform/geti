// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Text, View } from '@adobe/react-spectrum';

import { CANVAS_ADJUSTMENTS_KEYS } from '../../../../../core/user-settings/dtos/user-settings.interface';
import { Switch } from '../../../../../shared/components/switch/switch.component';
import { UseCanvasSettingsState } from '../../../hooks/use-canvas-settings.hook';
import { AdjustmentAnnotation } from './adjustment-annotation.component';
import { AdjustmentImage } from './adjustment-image.component';

import classes from './canvas-adjustments.module.scss';

interface AdjustmentsListProps {
    canvasSettingsConfig: UseCanvasSettingsState;
}

export const AdjustmentsList = ({ canvasSettingsConfig }: AdjustmentsListProps): JSX.Element => {
    const [canvasSettings, handleCanvasSetting] = canvasSettingsConfig;

    const labelOpacity = Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.LABEL_OPACITY].value);
    const shouldHideLabels = Boolean(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.HIDE_LABELS].value);

    return (
        <View paddingEnd={'size-50'}>
            <Flex alignItems={'center'} justifyContent={'space-between'}>
                <Text>Hide labels</Text>
                <Flex alignItems={'center'} gap={'size-100'}>
                    <Switch
                        aria-label={'Hide labels'}
                        isSelected={shouldHideLabels}
                        onChange={(isSelected) => {
                            handleCanvasSetting(CANVAS_ADJUSTMENTS_KEYS.HIDE_LABELS, isSelected);
                        }}
                    />
                </Flex>
            </Flex>

            <Divider size={'S'} marginY={'size-250'} UNSAFE_className={classes.canvasAdjustmentsDivider} />

            <AdjustmentAnnotation
                headerText={'Label opacity'}
                formatOptions={{ style: 'percent' }}
                defaultValue={Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.LABEL_OPACITY].defaultValue)}
                value={labelOpacity}
                handleValueChange={(value) => {
                    handleCanvasSetting(CANVAS_ADJUSTMENTS_KEYS.LABEL_OPACITY, value);
                }}
                isDisabled={shouldHideLabels}
            />
            <AdjustmentAnnotation
                headerText={'Markers opacity'}
                formatOptions={{ style: 'percent' }}
                defaultValue={Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.MARKERS_OPACITY].defaultValue)}
                value={Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.MARKERS_OPACITY].value)}
                handleValueChange={(value) => {
                    handleCanvasSetting(CANVAS_ADJUSTMENTS_KEYS.MARKERS_OPACITY, value);
                }}
            />
            <AdjustmentAnnotation
                headerText={'Annotation fill opacity'}
                formatOptions={{ style: 'percent' }}
                defaultValue={Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.ANNOTATION_FILL_OPACITY].defaultValue)}
                value={Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.ANNOTATION_FILL_OPACITY].value)}
                handleValueChange={(value) => {
                    handleCanvasSetting(CANVAS_ADJUSTMENTS_KEYS.ANNOTATION_FILL_OPACITY, value);
                }}
            />
            <AdjustmentAnnotation
                headerText={'Annotation border opacity'}
                formatOptions={{ style: 'percent' }}
                defaultValue={Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.ANNOTATION_BORDER_OPACITY].defaultValue)}
                value={Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.ANNOTATION_BORDER_OPACITY].value)}
                handleValueChange={(value) => {
                    handleCanvasSetting(CANVAS_ADJUSTMENTS_KEYS.ANNOTATION_BORDER_OPACITY, value);
                }}
            />
            <Divider size={'S'} marginY={'size-250'} UNSAFE_className={classes.canvasAdjustmentsDivider} />
            <AdjustmentImage
                headerText={'Image brightness'}
                formatOptions={{ signDisplay: 'exceptZero' }}
                defaultValue={Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.IMAGE_BRIGHTNESS].defaultValue)}
                value={Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.IMAGE_BRIGHTNESS].value)}
                handleValueChange={(value) => {
                    handleCanvasSetting(CANVAS_ADJUSTMENTS_KEYS.IMAGE_BRIGHTNESS, value);
                }}
            />
            <AdjustmentImage
                headerText={'Image contrast'}
                formatOptions={{ signDisplay: 'exceptZero' }}
                defaultValue={Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.IMAGE_CONTRAST].defaultValue)}
                value={Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.IMAGE_CONTRAST].value)}
                handleValueChange={(value) => {
                    handleCanvasSetting(CANVAS_ADJUSTMENTS_KEYS.IMAGE_CONTRAST, value);
                }}
            />
            <AdjustmentImage
                headerText={'Image saturation'}
                formatOptions={{ signDisplay: 'exceptZero' }}
                defaultValue={Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.IMAGE_SATURATION].defaultValue)}
                value={Number(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.IMAGE_SATURATION].value)}
                handleValueChange={(value) => {
                    handleCanvasSetting(CANVAS_ADJUSTMENTS_KEYS.IMAGE_SATURATION, value);
                }}
            />
            <Divider size={'S'} marginY={'size-250'} UNSAFE_className={classes.canvasAdjustmentsDivider} />

            <Flex alignItems={'center'} justifyContent={'space-between'}>
                <Text>Pixel view</Text>
                <Flex alignItems={'center'} gap={'size-100'}>
                    <Switch
                        aria-label={'Pixel view'}
                        isSelected={Boolean(canvasSettings[CANVAS_ADJUSTMENTS_KEYS.PIXEL_VIEW].value)}
                        onChange={(isSelected) => {
                            handleCanvasSetting(CANVAS_ADJUSTMENTS_KEYS.PIXEL_VIEW, isSelected);
                        }}
                    />
                </Flex>
            </Flex>
        </View>
    );
};
