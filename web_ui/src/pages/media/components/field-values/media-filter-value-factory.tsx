// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SearchRuleField, SearchRuleValue } from '../../../../core/media/media-filter.interface';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { MediaFilterValueAnnotationSceneState } from './media-filter-value-annotation-scene-state.component';
import { MediaFilterValueDate } from './media-filter-value-date.component';
import { MediaFilterValueLabel } from './media-filter-value-label.component';
import { MediaFilterValueShapeAreaPercentage } from './media-filter-value-shape-area-percentage.component';
import { MediaFilterValueShape } from './media-filter-value-shape.component';
import { MediaFilterValueType } from './media-filter-value-type.component';
import { MediaFilterValueUsersList } from './media-filter-value-users-list';
import { MediaIntegerField } from './media-integer-field.component';
import { MediaTextField } from './media-text-field.component';

interface MediaFilterValueFactoryProps {
    isDisabled?: boolean;
    value: SearchRuleValue;
    field: SearchRuleField | '';
    isAnomalyProject: boolean;
    isMultiselection?: boolean;
    isDatasetAccordion?: boolean;
    onSelectionChange: (key: SearchRuleValue) => void;
}

export const MediaFilterValueFactory = (props: MediaFilterValueFactoryProps): JSX.Element => {
    const { isTaskChainProject } = useProject();

    switch (props.field) {
        case SearchRuleField.MediaSize:
        case SearchRuleField.MediaWidth:
        case SearchRuleField.MediaHeight:
        case SearchRuleField.ShapeAreaPixel:
            const { value, isDisabled, onSelectionChange } = props;

            return (
                <MediaIntegerField
                    isDisabled={isDisabled}
                    initialValue={(value as number) || 0}
                    ariaLabel={
                        props.field == SearchRuleField.ShapeAreaPixel
                            ? 'Media filter shape area pixel'
                            : 'Media filter size'
                    }
                    onSelectionChange={onSelectionChange}
                />
            );

        case SearchRuleField.LabelId:
            return (
                <MediaFilterValueLabel
                    {...props}
                    value={props.value as string}
                    isDisabled={props.isAnomalyProject && !props.isDatasetAccordion}
                />
            );

        case SearchRuleField.AnnotationSceneState:
            return (
                <MediaFilterValueAnnotationSceneState
                    {...props}
                    value={props.value as string}
                    isTaskChainProject={isTaskChainProject}
                    isAnomalyProject={props.isAnomalyProject}
                />
            );

        case SearchRuleField.MediaUploadDate:
        case SearchRuleField.AnnotationCreationDate:
            return <MediaFilterValueDate {...props} value={props.value as string} />;

        case SearchRuleField.MediaType:
            return <MediaFilterValueType {...props} />;
        case SearchRuleField.ShapeType:
            return <MediaFilterValueShape {...props} />;

        case SearchRuleField.ShapeAreaPercentage:
            return <MediaFilterValueShapeAreaPercentage {...props} />;

        case SearchRuleField.UserName:
            return <MediaFilterValueUsersList {...props} />;

        default:
            return (
                <MediaTextField
                    {...props}
                    isDisabled={props.field === ''}
                    value={props.value as string}
                    ariaLabel={'media-filter-name'}
                />
            );
    }
};
