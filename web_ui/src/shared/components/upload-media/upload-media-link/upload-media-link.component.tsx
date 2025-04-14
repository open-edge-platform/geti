// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useRef } from 'react';

import { isFirefox } from '@react-aria/utils';
import { dimensionValue } from '@react-spectrum/utils';

import { mediaExtensionHandler } from '../../../../providers/media-upload-provider/media-upload.validator';
import { CANT_UPLOAD_FOLDER_FIREFOX } from '../../../custom-notification-messages';
import { VALID_MEDIA_TYPES_DISPLAY } from '../../../media-utils';
import { LinkButton } from '../../link-button/link-button.component';
import { MenuTriggerLink } from '../../menu-trigger/menu-trigger-link/menu-trigger-link.component';
import { MenuItemsKey } from '../upload-media-button/upload-media-button.interface';
import { useOnFileInputChange } from '../useFileInputChange.hook';
import { onMenuAction } from '../utils';

interface UploadMediaLinkProps {
    id: string;
    text: string;
    uploadCallback: (files: File[]) => void;
    acceptedFormats?: string;
    multiple?: boolean;
    ariaLabel?: string;
    isDisabled?: boolean;
}

export const UploadMediaLink = ({
    id,
    text,
    ariaLabel,
    acceptedFormats,
    multiple = true,
    isDisabled = false,
    uploadCallback,
}: UploadMediaLinkProps): JSX.Element => {
    const { onFileInputChange } = useOnFileInputChange({ uploadCallback });

    const fileInputRef = useRef<HTMLInputElement>({} as HTMLInputElement);

    // Disabled folder option if the user is using Firefox
    const isFolderOptionDisabled = isFirefox();

    const onMenuActionHandler = (key: Key) => onMenuAction(key, fileInputRef);

    return (
        <>
            <input
                hidden
                multiple={multiple}
                type='file'
                ref={fileInputRef}
                onChange={onFileInputChange}
                aria-label={`${ariaLabel} upload media input`}
                style={{ pointerEvents: 'all' }}
                onClick={() => (fileInputRef.current.value = '')}
                accept={acceptedFormats ?? mediaExtensionHandler(VALID_MEDIA_TYPES_DISPLAY)}
            />
            {multiple ? (
                <MenuTriggerLink
                    id={id}
                    text={text}
                    menuTooltip={CANT_UPLOAD_FOLDER_FIREFOX}
                    disabledKeys={isFolderOptionDisabled ? [MenuItemsKey.FOLDER.toLocaleLowerCase()] : undefined}
                    items={[MenuItemsKey.FILES, MenuItemsKey.FOLDER]}
                    onAction={onMenuActionHandler}
                    ariaLabel={ariaLabel}
                    isDisabled={isDisabled}
                />
            ) : (
                <LinkButton
                    text={text}
                    onPress={() => onMenuActionHandler(MenuItemsKey.FILE)}
                    ariaLabel={ariaLabel}
                    UNSAFE_style={{ fontSize: dimensionValue('size-225') }}
                />
            )}
        </>
    );
};
