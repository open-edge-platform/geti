// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ChevronLeft, ChevronRight } from '../../../../../../assets/icons';
import { ActionButton } from '../../../../button/button.component';

import classes from './image-preview-control.module.scss';

export enum ControlType {
    NEXT = 'next',
    PREVIOUS = 'previous',
}

interface ImagePreviewControlProps {
    type: ControlType;
    onClick: () => void;
}

const imageStyle = {
    width: '32px',
    height: '32px',
    fillOpacity: 0.38,
};

export const ImagePreviewControl = ({ type, onClick }: ImagePreviewControlProps): JSX.Element => {
    const position =
        type === ControlType.NEXT
            ? {
                  right: 0,
              }
            : {
                  left: 0,
              };

    return (
        <ActionButton
            height='100%'
            width={{ base: 'size-500', L: 'size-1000' }}
            aria-label={`${type} preview navigation`}
            id={`${type}-preview-navigation-id`}
            position='absolute'
            onPress={onClick}
            UNSAFE_className={classes.navigationButton}
            UNSAFE_style={{
                ...position,
            }}
        >
            {type === ControlType.NEXT ? <ChevronRight {...imageStyle} /> : <ChevronLeft {...imageStyle} />}
        </ActionButton>
    );
};
