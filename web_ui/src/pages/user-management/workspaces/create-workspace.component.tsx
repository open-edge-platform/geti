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

import { Heading, Text, View } from '@adobe/react-spectrum';

import { CreateWorkspaceDialog } from './create-workspace-dialog.component';

export const CreateWorkspace = (): JSX.Element => {
    return (
        <View>
            <Heading level={6} margin={0}>
                New workspace
            </Heading>
            <Text>Bring your ideas, projects, and teams together in one place.</Text>
            <CreateWorkspaceDialog />
        </View>
    );
};
