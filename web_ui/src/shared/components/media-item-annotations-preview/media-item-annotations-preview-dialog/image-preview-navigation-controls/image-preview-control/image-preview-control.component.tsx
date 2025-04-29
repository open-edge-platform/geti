// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
