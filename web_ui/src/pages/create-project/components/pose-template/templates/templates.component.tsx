// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Item, Key, Menu, MenuTrigger, Section } from '@adobe/react-spectrum';
import { Button } from '@geti/ui';

import { JointConnection } from '../../../../../assets/icons';
import { RegionOfInterest } from '../../../../../core/annotations/annotation.interface';
import { isNonEmptyArray } from '../../../../../shared/utils';
import { useGetProjectsTemplates } from '../hooks/use-get-projects-templates.hook';
import { TemplateState } from '../util';
import { animalPose } from './animal-pose.template';
import { humanFace } from './human-face.template';
import { humanPose } from './human-pose.template';
import {
    formatTemplate,
    getGetiTemplateKey,
    getGetiTemplateName,
    getProjectTemplateKey,
    getProjectTemplateName,
    isGetiTemplate,
    isProjectTemplate,
    RawStructure,
    TemplatePose,
} from './utils';

interface TemplatesProps {
    roi: RegionOfInterest;
    onAction: (template: TemplateState) => void;
}

const predefinedTemplateMapper: Record<TemplatePose, RawStructure> = {
    [TemplatePose.HumanPose]: humanPose,
    [TemplatePose.HumanFace]: humanFace,
    [TemplatePose.AnimalPose]: animalPose,
};

export const Templates = ({ roi, onAction }: TemplatesProps) => {
    const projectTemplates = useGetProjectsTemplates();

    const handleAction = (templateKey: Key) => {
        if (isGetiTemplate(templateKey)) {
            onAction(formatTemplate(predefinedTemplateMapper[getGetiTemplateName(templateKey)], roi));
        }

        if (isProjectTemplate(templateKey)) {
            const selectedTemplate = projectTemplates.find(({ name }) => name === getProjectTemplateName(templateKey));

            selectedTemplate && onAction(formatTemplate(selectedTemplate?.template, roi));
        }
    };

    return (
        <MenuTrigger aria-label='templates menu'>
            <Button variant={'secondary'} maxWidth={'size-3000'} aria-label='templates list'>
                <Flex gap={'size-75'} alignItems={'center'}>
                    <JointConnection />
                    Templates
                </Flex>
            </Button>
            <Menu onAction={handleAction} maxHeight={'size-6000'}>
                <Section title='Geti templates'>
                    {Object.keys(predefinedTemplateMapper).map((name) => (
                        <Item key={getGetiTemplateKey(name)} textValue={name}>
                            {name}
                        </Item>
                    ))}
                </Section>

                {isNonEmptyArray(projectTemplates) ? (
                    <Section title='Project templates'>
                        {projectTemplates.map(({ name }) => (
                            <Item key={getProjectTemplateKey(name)} textValue={name}>
                                {name}
                            </Item>
                        ))}
                    </Section>
                ) : null}
            </Menu>
        </MenuTrigger>
    );
};
