// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode } from 'react';

import { screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { DatasetImportToNewProjectProvider } from '../../providers/dataset-import-to-new-project-provider/dataset-import-to-new-project-provider.component';
import { ProjectsImportProvider } from '../../providers/projects-import-provider/projects-import-provider.component';
import { applicationRender as render } from '../../test-utils/application-provider-render';
import { ProjectImportPanel } from './import-project-panel.component';

const Wrapper = ({ children }: { children: ReactNode }) => {
    return (
        <DatasetImportToNewProjectProvider>
            <ProjectsImportProvider>{children}</ProjectsImportProvider>
        </DatasetImportToNewProjectProvider>
    );
};

describe('ImportProjectPanel', () => {
    it('It allows the user to import an exported project', async () => {
        const onImport = jest.fn();
        await render(
            <Wrapper>
                <ProjectImportPanel
                    onImportProject={onImport}
                    options={{ keepOriginalDates: false, projectName: '', skipSignatureVerification: true }}
                />
            </Wrapper>
        );

        const upload = screen.getByRole('button', { name: 'Upload' });
        expect(upload).toBeInTheDocument();

        const file = new File(['Card detection'], 'card-detection.zip', { type: 'application/x-zip' });
        const uploadFileElement = screen.getByLabelText('upload-media-input');

        await userEvent.upload(uploadFileElement, [file]);

        await waitFor(() => {
            expect(onImport).toHaveBeenCalled();
        });
    });

    it('It shows an error when importing a non zip file', async () => {
        const onImport = jest.fn();
        await render(
            <Wrapper>
                <ProjectImportPanel
                    onImportProject={onImport}
                    options={{ keepOriginalDates: false, projectName: '', skipSignatureVerification: true }}
                />
            </Wrapper>
        );

        const upload = screen.getByRole('button', { name: 'Upload' });
        expect(upload).toBeInTheDocument();

        const file = new File(['Card'], 'card.png', { type: 'image/png' });
        const uploadFileElement = screen.getByLabelText('upload-media-input');

        const user = userEvent.setup({ applyAccept: false });
        await user.upload(uploadFileElement, [file]);

        await screen.findByText('Invalid file extension, please try again');

        expect(onImport).not.toHaveBeenCalled();
    });
});
