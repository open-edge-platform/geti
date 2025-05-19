// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, FormEvent, forwardRef, ReactNode, useCallback, useEffect, useMemo, useState } from 'react';

import { TextField } from '@geti/ui';
import { TextFieldRef } from '@react-types/textfield';
import { isEmpty, isFunction } from 'lodash-es';
import { useFilter } from 'react-aria';

import {
    fetchLabelsTree,
    findLabelParents,
    uniqueLabels,
} from '../../../../../core/labels/annotator-utils/labels-utils';
import { LabelTreeLabelProps } from '../../../../../core/labels/label-tree-view.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { getIds, onEscape } from '../../../../../shared/utils';
import { LabelResultPanel } from './label-result-panel.component';
import { SearchLabelTreeItemSuffix } from './search-label-tree-view-item.component';

const useFilteredResults = (input: string, labels: ReadonlyArray<Label>) => {
    const { contains } = useFilter({ sensitivity: 'base' });
    return useMemo((): LabelTreeLabelProps[] => {
        const emptyInput = isEmpty(input.trim());

        const matchLabels = emptyInput ? labels : labels.filter((label: Label) => contains(label.name, input));

        const parents: Label[] = matchLabels.flatMap((label: Label) => findLabelParents(labels, label));
        const resultLabels: Label[] = uniqueLabels(matchLabels.concat(parents));

        const openNodes = emptyInput ? [] : getIds(resultLabels);

        return fetchLabelsTree(resultLabels, openNodes);
        // contains changes on every render
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [input, labels]);
};

const NoopResultWrapper = ({ children }: { children: ReactNode }) => {
    return <>{children}</>;
};

interface BaseLabelSearchProps {
    id?: string;
    labels: ReadonlyArray<Label>;
    onClick: (label: Label | null) => void;
    className?: string;
    dontFocusOnMount?: boolean;
    textFieldProps?: ComponentProps<typeof TextField>;
    ResultWrapper?: (props: { children: ReactNode }) => JSX.Element;
    suffix?: SearchLabelTreeItemSuffix;
    prefix?: SearchLabelTreeItemSuffix;
    resultWrapperProps?: object;
}
export const BaseLabelSearch = forwardRef<TextFieldRef, BaseLabelSearchProps>(
    (
        {
            id,
            labels,
            onClick,
            dontFocusOnMount = false,
            className = undefined,
            textFieldProps = {},
            ResultWrapper = NoopResultWrapper,
            resultWrapperProps,
            suffix,
            prefix,
        },
        ref
    ): JSX.Element => {
        const [input, setInput] = useState(textFieldProps.value ?? '');

        const results = useFilteredResults(input, labels);

        const treeItemClickHandler = useCallback(
            (label: Label): void => {
                onClick(label);
                setInput('');
            },
            [onClick]
        );

        const handleInput = (event: FormEvent<HTMLInputElement>) => {
            setInput(event.currentTarget.value);
        };

        useEffect(() => {
            if (ref && !isFunction(ref) && ref.current && !dontFocusOnMount) {
                ref.current.focus();
            }
        }, [dontFocusOnMount, ref]);

        return (
            <div className={className}>
                <TextField
                    id={id ? `${id}-label-search-field-id` : 'label-search-field-id'}
                    onKeyDown={onEscape((event) => {
                        setInput('');
                        event.currentTarget.blur();
                    })}
                    {...{
                        width: '100%',
                        placeholder: 'Select label',
                        'aria-label': 'Select label',
                        ...textFieldProps,
                    }}
                    ref={ref}
                    value={input}
                    onInput={handleInput}
                />

                <ResultWrapper {...resultWrapperProps}>
                    <LabelResultPanel
                        suffix={suffix}
                        prefix={prefix}
                        labelsTree={results}
                        onSelected={treeItemClickHandler}
                    />
                </ResultWrapper>
            </div>
        );
    }
);
