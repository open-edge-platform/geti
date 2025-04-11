// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
