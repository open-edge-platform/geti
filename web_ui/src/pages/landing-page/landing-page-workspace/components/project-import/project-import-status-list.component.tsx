// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AnimatePresence, motion } from 'framer-motion';

import { ProjectImportStatusValues } from '../../../../../providers/projects-import-provider/project-import.interface';
import { useProjectsImportProvider } from '../../../../../providers/projects-import-provider/projects-import-provider.component';
import { ANIMATION_PARAMETERS } from '../../../../../shared/animation-parameters/animation-parameters';
import { ProjectCreationStatus } from './project-creation-status.component';
import { ProjectImportInterrupted } from './project-import-interrupted.component';
import { ProjectImportStatus } from './project-import-status.component';

import classes from './project-import.module.scss';

export const ProjectImportStatusList = (): JSX.Element => {
    const { importItems } = useProjectsImportProvider();

    return (
        <AnimatePresence>
            {Object.values(importItems)
                .filter(({ status }) =>
                    [
                        ProjectImportStatusValues.CREATING,
                        ProjectImportStatusValues.IMPORTING,
                        ProjectImportStatusValues.IMPORTING_INTERRUPTED,
                    ].includes(status)
                )
                .map((item) => {
                    return (
                        <motion.div
                            key={item.fileId}
                            exit={'hidden'}
                            initial={'hidden'}
                            animate={'visible'}
                            layoutId={'project-import-status'}
                            className={classes.statusContainer}
                            variants={ANIMATION_PARAMETERS.ANIMATE_LIST}
                        >
                            {item.status === ProjectImportStatusValues.IMPORTING && (
                                <ProjectImportStatus importItem={item} />
                            )}
                            {item.status === ProjectImportStatusValues.IMPORTING_INTERRUPTED && (
                                <ProjectImportInterrupted importItem={item} />
                            )}
                            {item.status === ProjectImportStatusValues.CREATING && (
                                <ProjectCreationStatus importItem={item} />
                            )}
                        </motion.div>
                    );
                })}
        </AnimatePresence>
    );
};
