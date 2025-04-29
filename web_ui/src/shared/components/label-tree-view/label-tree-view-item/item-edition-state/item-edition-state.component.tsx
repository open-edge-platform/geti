// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text, View } from '@adobe/react-spectrum';

import { COLOR_MODE } from '../../../../../assets/icons/color-mode.enum';
import { LabelItemEditionState } from '../../../../../core/labels/label-tree-view.interface';
import { ColorThumb } from '../../../color-thumb/color-thumb.component';
import { isNewState } from '../utils';

interface ItemEditionStateProps {
    state: LabelItemEditionState;
    idSuffix: string;
}

export const ItemEditionState = ({ state, idSuffix }: ItemEditionStateProps): JSX.Element => {
    let color;
    const editionState = isNewState(state) ? LabelItemEditionState.NEW : state;

    if (editionState === LabelItemEditionState.IDLE) {
        return <></>;
    }

    switch (editionState) {
        case LabelItemEditionState.NEW:
            color = COLOR_MODE.POSITIVE;
            break;
        case LabelItemEditionState.REMOVED:
            color = COLOR_MODE.NEGATIVE;
            break;
        default:
            color = COLOR_MODE.WARNING;
    }

    return (
        <View
            borderRadius={'large'}
            UNSAFE_style={{ height: 'fit-content' }}
            backgroundColor={'gray-200'}
            paddingX={'size-75'}
            paddingEnd={'size-125'}
        >
            <Flex width={'100%'} gap={'size-75'} justifyContent={'space-between'} alignItems={'center'}>
                <ColorThumb
                    size={8}
                    color={color}
                    id={`label-state-${editionState}-${idSuffix}`}
                    borderRadius={'large'}
                />
                <Text UNSAFE_style={{ fontSize: '11px', whiteSpace: 'nowrap' }}>{editionState}</Text>
            </Flex>
        </View>
    );
};
