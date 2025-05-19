// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, SVGProps } from 'react';

import { dimensionValue, Heading, Image, Radio, RadioGroup, Text, View } from '@geti/ui';
import { isString } from 'lodash-es';
import { usePress } from 'react-aria';

import classes from './card.module.scss';

type CardProps = CardWithImageProps | CardWithTitleProps;

interface CardCommonProps {
    id: string;
    title?: string;
    isLargeSize?: boolean;
    description?: string;
    isSelected: boolean;
    isDisabled?: boolean;
    onPress: () => void;
}

interface CardWithTitleProps extends CardCommonProps {
    titleComponent: JSX.Element;
}

interface CardWithImageProps extends CardCommonProps {
    alt: string;
    TaskTypeIcon: FC<SVGProps<SVGSVGElement>> | string;
    imgBoxes?: JSX.Element;
}

export const Card = ({
    id,
    isSelected,
    title = '',
    description = '',
    onPress,
    isDisabled = false,
    isLargeSize = true,
    ...headerProps
}: CardProps): JSX.Element => {
    const hasImage = 'TaskTypeIcon' in headerProps;

    const { pressProps } = usePress({
        onPress,
    });

    return (
        <div
            {...pressProps}
            id={id}
            data-testid={id}
            className={`${isSelected ? classes.selected : classes.card} ${isDisabled ? classes.disabled : ''}`}
            aria-label={title}
        >
            <div role='figure'>
                {hasImage ? (
                    <div className={classes.coverPhoto}>
                        {headerProps.imgBoxes ? <div className={classes.boxes}>{headerProps.imgBoxes}</div> : ''}
                        {isString(headerProps.TaskTypeIcon) ? (
                            <Image
                                alt={headerProps.alt}
                                src={headerProps.TaskTypeIcon}
                                UNSAFE_style={{ display: 'flex', justifyContent: 'center' }}
                            />
                        ) : (
                            <headerProps.TaskTypeIcon aria-label={headerProps.alt} />
                        )}
                    </div>
                ) : (
                    headerProps.titleComponent
                )}

                <View
                    isHidden={!title && !description}
                    height='size-1250'
                    backgroundColor='gray-100'
                    UNSAFE_className={classes.cardBody}
                    padding={'size-175'}
                >
                    {title && (
                        <Heading marginTop={0} marginBottom='size-50' level={6}>
                            <RadioGroup value={isSelected ? title : ''} onChange={onPress} aria-label={title}>
                                <Radio value={title} UNSAFE_className={classes.cardRadioBtn}>
                                    {title}
                                </Radio>
                            </RadioGroup>
                        </Heading>
                    )}

                    <Text
                        UNSAFE_style={{
                            display: 'inline-block',
                            fontSize: isLargeSize ? 'inherit' : dimensionValue('size-160'),
                            lineHeight: isLargeSize ? 'inherit' : dimensionValue('size-225'),
                        }}
                    >
                        {description}
                    </Text>
                </View>
            </div>
        </div>
    );
};
