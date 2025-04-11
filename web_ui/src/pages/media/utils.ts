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

import { KeyboardEvent } from 'react';

import { InfiniteData } from '@tanstack/react-query';
import differenceBy from 'lodash/differenceBy';
import get from 'lodash/get';
import isEmpty from 'lodash/isEmpty';
import isEqual from 'lodash/isEqual';
import { v4 as uuidv4 } from 'uuid';

import { Label } from '../../core/labels/label.interface';
import { Image, ImageIdentifier } from '../../core/media/image.interface';
import {
    AdvancedFilterOptions,
    AnnotationSceneState,
    FilterItems,
    MediaFilterOptions,
    MediaTypeOption,
    SearchOptionsRule,
    SearchRuleField,
    SearchRuleMediaType,
    SearchRuleOperator,
    SearchRuleShapeType,
    SearchRuleValue,
    ShapeOption,
} from '../../core/media/media-filter.interface';
import { MediaAdvancedFilterResponse } from '../../core/media/media.interface';
import {
    isVideo,
    isVideoFrame,
    Video,
    VideoFrame,
    VideoFrameIdentifier,
    VideoIdentifier,
} from '../../core/media/video.interface';
import { KeyMap } from '../../shared/keyboard-events/keyboard.interface';
import { hasDifferentId, hasEqualId, isDifferent } from '../../shared/utils';

export const textRegex = /[a-zA-Z0-9]+/;
export const lastCommaRegex = /,\s*$/;
export const isValidInteger = (num: number | undefined) => num != undefined && num <= Number.MAX_SAFE_INTEGER;

type OptionsKeys =
    | SearchRuleOperator
    | SearchRuleField
    | AnnotationSceneState
    | SearchRuleShapeType
    | SearchRuleMediaType;

const SEARCH_BY_NAME_ID = 'search-rule-id';

export const OPERATOR_OPTIONS: { key: SearchRuleOperator; text: string; fields: SearchRuleField[] }[] = [
    {
        key: SearchRuleOperator.In,
        text: 'In',
        fields: [SearchRuleField.LabelId, SearchRuleField.ShapeType, SearchRuleField.AnnotationSceneState],
    },
    { key: SearchRuleOperator.NotIn, text: 'Not In', fields: [SearchRuleField.LabelId, SearchRuleField.ShapeType] },
    {
        key: SearchRuleOperator.Equal,
        text: 'Equal',
        fields: [
            SearchRuleField.MediaWidth,
            SearchRuleField.MediaHeight,
            SearchRuleField.MediaName,
            SearchRuleField.MediaType,
            SearchRuleField.AnnotationSceneState,
            SearchRuleField.ShapeType,
            SearchRuleField.UserName,
        ],
    },
    {
        key: SearchRuleOperator.NotEqual,
        text: 'Not Equal',
        fields: [
            SearchRuleField.MediaWidth,
            SearchRuleField.MediaHeight,
            SearchRuleField.MediaName,
            SearchRuleField.ShapeType,
            SearchRuleField.UserName,
        ],
    },
    {
        key: SearchRuleOperator.Less,
        text: 'Less',
        fields: [
            SearchRuleField.MediaWidth,
            SearchRuleField.MediaHeight,
            SearchRuleField.ShapeAreaPercentage,
            SearchRuleField.ShapeAreaPixel,
            SearchRuleField.MediaSize,
        ],
    },
    {
        key: SearchRuleOperator.Less,
        text: 'Earlier than',
        fields: [SearchRuleField.AnnotationCreationDate, SearchRuleField.MediaUploadDate],
    },
    {
        key: SearchRuleOperator.LessOrEqual,
        text: 'Less or equal',
        fields: [
            SearchRuleField.MediaWidth,
            SearchRuleField.MediaHeight,
            SearchRuleField.ShapeAreaPercentage,
            SearchRuleField.ShapeAreaPixel,
            SearchRuleField.MediaSize,
        ],
    },
    {
        key: SearchRuleOperator.Greater,
        text: 'Greater',
        fields: [
            SearchRuleField.MediaWidth,
            SearchRuleField.MediaHeight,
            SearchRuleField.ShapeAreaPercentage,
            SearchRuleField.ShapeAreaPixel,
            SearchRuleField.MediaSize,
        ],
    },
    {
        key: SearchRuleOperator.Greater,
        text: 'Later than',
        fields: [SearchRuleField.AnnotationCreationDate, SearchRuleField.MediaUploadDate],
    },
    {
        key: SearchRuleOperator.GreaterOrEqual,
        text: 'Greater or equal',
        fields: [
            SearchRuleField.MediaWidth,
            SearchRuleField.MediaHeight,
            SearchRuleField.ShapeAreaPercentage,
            SearchRuleField.ShapeAreaPixel,
            SearchRuleField.MediaSize,
        ],
    },
    {
        key: SearchRuleOperator.Contains,
        text: 'Contains',
        fields: [SearchRuleField.MediaName],
    },
];

export const FIELD_OPTIONS: FilterItems[][] = [
    [{ key: SearchRuleField.LabelId, text: 'Label' }],
    [
        { key: SearchRuleField.AnnotationSceneState, text: 'Annotation status' },
        { key: SearchRuleField.AnnotationCreationDate, text: 'Annotation creation date' },
        { key: SearchRuleField.UserName, text: 'Annotation creator' },
    ],
    [
        { key: SearchRuleField.MediaSize, text: 'Media size' },
        { key: SearchRuleField.MediaType, text: 'Media type' },
        { key: SearchRuleField.MediaHeight, text: 'Media height' },
        { key: SearchRuleField.MediaWidth, text: 'Media width' },
        { key: SearchRuleField.MediaUploadDate, text: 'Media upload date' },
        { key: SearchRuleField.MediaName, text: 'Media name' },
    ],
    [
        { key: SearchRuleField.ShapeType, text: 'Shape type' },
        { key: SearchRuleField.ShapeAreaPercentage, text: 'Shape area percentage' },
        { key: SearchRuleField.ShapeAreaPixel, text: 'Shape area pixel' },
    ],
];

export const ANNOTATION_SCENE_OPTIONS: { key: AnnotationSceneState; text: string }[] = [
    { key: AnnotationSceneState.NONE, text: 'Unannotated' },
    { key: AnnotationSceneState.ANNOTATED, text: 'Annotated' },
    { key: AnnotationSceneState.PARTIALLY_ANNOTATED, text: 'Partially annotated' },
    { key: AnnotationSceneState.REVISIT, text: 'Revisit' },
];

export const SHAPE_OPTIONS: ShapeOption[] = [
    {
        key: SearchRuleShapeType.ELLIPSE,
        text: 'Circle',
    },
    {
        key: SearchRuleShapeType.POLYGON,
        text: 'Polygon',
    },
    {
        key: SearchRuleShapeType.RECTANGLE,
        text: 'Rectangle',
    },
];

export const MEDIA_TYPE_OPTIONS: MediaTypeOption[] = [
    {
        key: SearchRuleMediaType.IMAGE,
        text: 'Image',
    },
    {
        key: SearchRuleMediaType.VIDEO,
        text: 'Video',
    },
];

export const isDigit = (keyCode: number): boolean => keyCode >= 48 && keyCode <= 90;

export const hasLabelsDifference = (labels: Label[], otherLabels: Label[]): boolean =>
    !isEmpty(differenceBy(labels, otherLabels, 'id'));

export const isEmptyRule = ({ value, field, operator }: SearchOptionsRule): boolean =>
    [value, field, operator].some((val) => val === '' || val === undefined);

export const isUniqueRule = (newRule: SearchOptionsRule, rules: SearchOptionsRule[]): boolean =>
    rules.every((currentRule) => !isEqual(newRule, currentRule));

export const findLabelsById = (ids: string[], labels: Label[]): Label[] =>
    ids.map((id) => labels.find(hasEqualId(id)) as Label).filter((label) => Boolean(label));

export const removeFilterRule = (
    filterOptions: AdvancedFilterOptions,
    newRule: SearchOptionsRule
): AdvancedFilterOptions => {
    if (isEmpty(filterOptions)) {
        return {};
    }

    const filteredRules = filterOptions.rules.filter(hasDifferentId(newRule.id));

    if (isEmpty(filteredRules)) {
        return {};
    }

    return {
        condition: 'and',
        rules: filteredRules,
    };
};

export const getUpdatedRule = (updatedRule: SearchOptionsRule): SearchOptionsRule => {
    const baseSearchRule = buildSearchRule('');
    const hasSearchRuleId = updatedRule.id === baseSearchRule.id;
    const isSearchRuleOverwrite =
        hasSearchRuleId &&
        !(updatedRule.field === baseSearchRule.field && updatedRule.operator === baseSearchRule.operator);

    if (isSearchRuleOverwrite) {
        return { ...updatedRule, id: uuidv4() };
    } else {
        return updatedRule;
    }
};

export const buildSearchRule = (value: string) => ({
    field: SearchRuleField.MediaName,
    operator: SearchRuleOperator.Contains,
    value,
    id: SEARCH_BY_NAME_ID,
});

export const getSearchRuleValue = (mediaFilterOptions: AdvancedFilterOptions): string => {
    const searchRule = mediaFilterOptions.rules?.find(hasEqualId(SEARCH_BY_NAME_ID));

    // In this case we know that if searchRule was found, the value would be string
    return !isEmpty(searchRule) ? (searchRule?.value as string) : '';
};

export const addOrUpdateFilterRule = (
    filterOptions: AdvancedFilterOptions,
    newRule: SearchOptionsRule
): AdvancedFilterOptions => {
    if (isEmpty(filterOptions)) {
        return {
            condition: 'and',
            rules: [newRule],
        };
    }

    const filteredRules = filterOptions.rules.filter(hasDifferentId(newRule.id));
    return {
        condition: 'and',
        rules: [...filteredRules, newRule],
    };
};

export const removeRuleById = (filterOptions: AdvancedFilterOptions, filterId: string): AdvancedFilterOptions => {
    if (isEmpty(filterOptions)) {
        return {};
    }

    const filteredRules = filterOptions.rules.filter(hasDifferentId(filterId));

    if (isEmpty(filteredRules)) {
        return {};
    }

    return {
        condition: 'and',
        rules: filteredRules,
    };
};

export const getValidRules = (rules: SearchOptionsRule[] = []) =>
    rules.filter((rule, index) => {
        const untestedRules = rules.slice(index + 1, rules.length + 1);

        return !isEmptyRule(rule) && isUniqueRule(rule, untestedRules);
    });

export const getRuleByField = (rules: SearchOptionsRule[] = [], field: SearchRuleField) =>
    rules.filter((rule) => rule.field === field);

const getByKey =
    <T extends { key: OptionsKeys }>(options: T[]) =>
    (key: OptionsKeys) =>
        options.find((operator) => operator.key === key);

export const getShapeTypeByKey = getByKey(SHAPE_OPTIONS);
const getMediaTypeByKey = getByKey(MEDIA_TYPE_OPTIONS);
export const getAnnotationSceneByKey = getByKey(ANNOTATION_SCENE_OPTIONS);

export const getShapesFromText = (text: SearchRuleValue) => {
    const shapes = (Array.isArray(text) ? [...text] : [String(text)]) as SearchRuleShapeType[];

    return shapes.map(getShapeTypeByKey) as ShapeOption[];
};

export const getTypesFromText = (text: SearchRuleValue) => {
    const types = (Array.isArray(text) ? [...text] : [String(text)]) as SearchRuleMediaType[];

    return types.map(getMediaTypeByKey) as MediaTypeOption[];
};

export const getAnnotationSceneStatesFromText = (text: SearchRuleValue) => {
    const statuses = (Array.isArray(text) ? [...text] : [String(text)]) as SearchRuleShapeType[];

    return statuses.map(getAnnotationSceneByKey) as typeof ANNOTATION_SCENE_OPTIONS;
};

export const deleteLastComa = (names: string): string => {
    return names.replace(lastCommaRegex, '').trim();
};

export const deleteEmptySpaceAndLastComa = (names: string): string => {
    //The regex "/\s*/g" can be replaced with replaceAll once our node version get updated ^14
    return deleteLastComa(names).replace(/\s*/g, '').trim();
};

export const getLowercaseSplitNames = (names: string): string[] => {
    const result = deleteEmptySpaceAndLastComa(names.toLowerCase()).split(',');

    return result[0] === '' ? [] : result;
};
export const getLowercaseTrimmedText = (names: string): string[] => {
    return names
        .toLocaleLowerCase()
        .split(',')
        .map((name) => name.trim());
};

export const isKeyboardDelete = (event: KeyboardEvent): boolean =>
    event.code === KeyMap.Backspace || event.code === KeyMap.Delete;

export const concatByProperty = <T>(data: T[], property: keyof T): string =>
    data.reduce((accum, item) => `${accum}${get(item, property, '')}, `, '');

export const isDate = (value: SearchRuleField) =>
    [SearchRuleField.AnnotationCreationDate, SearchRuleField.MediaUploadDate].includes(value);

export const isLabelID = (value: SearchRuleField) => value === SearchRuleField.LabelId;
export const isShapeType = (value: SearchRuleField) => value === SearchRuleField.ShapeType;
export const isMediaType = (value: SearchRuleField) => value === SearchRuleField.MediaType;
export const isAnnotationScene = (value: SearchRuleField) => value === SearchRuleField.AnnotationSceneState;
export const isShapeAreaPercentage = (value: SearchRuleField) => value === SearchRuleField.ShapeAreaPercentage;

export const hasOnlyOneRuleAndIsEmpty = (rules: SearchOptionsRule[]): boolean => {
    return !isEmpty(rules) && rules.length === 1 && isEmptyRule(rules[0]);
};

export const getMediaId = (media: Video | Image | VideoFrame): string => {
    if (isVideo(media)) {
        return `video-${media.identifier.videoId}`;
    }

    if (isVideoFrame(media)) {
        return `video-${media.identifier.videoId}-${media.identifier.frameNumber}`;
    }

    return `image-${(media as Image).identifier.imageId}`;
};

export const getKeyConfig = <T extends { key: string; text: string }>(options: T[], toFindKey: string) => {
    const text = options.flat().find(({ key }) => key === toFindKey)?.text ?? 'Select an Option';

    return {
        text,
        isPlaceHolder: text === 'Select an Option',
    };
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const isMediaFilterOptions = (input: any): input is MediaFilterOptions => {
    return (
        input !== null &&
        typeof input === 'object' &&
        input.hasOwnProperty('condition') &&
        input.hasOwnProperty('rules') &&
        Array.isArray(input.rules)
    );
};

export const filterPageMedias = (
    currentData: InfiniteData<MediaAdvancedFilterResponse>,
    deletedIdentifiers: (ImageIdentifier | VideoIdentifier | VideoFrameIdentifier)[]
): InfiniteData<MediaAdvancedFilterResponse> => ({
    ...currentData,
    pages: currentData.pages.map((page) => ({
        ...page,
        media: page.media.filter((item) =>
            deletedIdentifiers.every((identifier) => isDifferent(identifier, item.identifier))
        ),
    })),
});
