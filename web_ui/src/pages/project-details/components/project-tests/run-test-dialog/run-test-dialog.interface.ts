// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ModelsGroups } from '../../../../../core/models/models.interface';
import { PreselectedModel } from '../../../project-details.interface';

export interface RunTestDialogProps {
    isOpen: boolean;
    handleClose: () => void;
    modelsGroups?: ModelsGroups[];
    preselectedModel?: PreselectedModel;
}

export type RunTestDialogContentProps = Omit<RunTestDialogProps, 'isOpen'>;
