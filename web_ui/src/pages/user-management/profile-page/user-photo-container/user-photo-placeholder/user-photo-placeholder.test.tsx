// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { render, screen } from '@testing-library/react';

import { UserPhotoPlaceholder } from './user-photo-placeholder.component';

describe('User photo placeholder and check if there is upload image link', () => {
    it('Show first letter of the name', () => {
        const userName = 'Admin';

        render(<UserPhotoPlaceholder email={'test@mail.com'} userName={userName} handleUploadClick={jest.fn()} />);

        expect(screen.getByTestId('placeholder-letter-id')).toHaveTextContent(userName.charAt(0));
        expect(screen.getByText('Upload image')).toBeInTheDocument();
    });

    it('Check if there is no upload image when upload is disabled', () => {
        const userName = 'Admin';

        render(
            <UserPhotoPlaceholder
                email={'test@mail.com'}
                userName={userName}
                handleUploadClick={jest.fn()}
                disableUpload={true}
            />
        );

        expect(screen.queryByText('Upload image')).not.toBeInTheDocument();
    });
});
