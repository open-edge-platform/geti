// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, FunctionComponent, PropsWithChildren } from 'react';

import { DialogTrigger } from '@adobe/react-spectrum';
import { Button, ButtonProps } from '@shared/components/button/button.component';

import { ReplaceOrMergeUserAnnotationsDialog } from './replace-or-merge-user-annotations-dialog.component';

interface PredictionButtonProps {
    id: string;
    variant: Exclude<ButtonProps['variant'], 'negative'>;
    merge: () => void;
    replace: () => void;
    userAnnotationsExist: boolean;
    isDisabled: boolean;
    styles?: CSSProperties;
}
export const PredictionButton: FunctionComponent<PropsWithChildren<PredictionButtonProps>> = ({
    children,
    id,
    merge,
    replace,
    variant,
    userAnnotationsExist,
    isDisabled,
    styles,
}): JSX.Element => {
    if (userAnnotationsExist) {
        return (
            <DialogTrigger>
                <Button
                    id={id}
                    variant={variant}
                    isDisabled={isDisabled}
                    aria-label={'Use predictions'}
                    UNSAFE_style={{ paddingTop: 'var(--spectrum-global-dimension-size-50)', ...styles }}
                >
                    {children}
                </Button>

                {(close): JSX.Element => (
                    <ReplaceOrMergeUserAnnotationsDialog close={close} merge={merge} replace={replace} />
                )}
            </DialogTrigger>
        );
    }

    return (
        <Button
            id={id}
            variant={variant}
            onPress={replace}
            isDisabled={isDisabled}
            aria-label={'use predictions'}
            UNSAFE_style={{ paddingTop: 'var(--spectrum-global-dimension-size-50)', ...styles }}
        >
            {children}
        </Button>
    );
};
