import React, { Fragment, useState } from 'react';
import { Combobox, Transition } from '@headlessui/react';
import { Check, ChevronDown, Search } from 'lucide-react';

interface Option {
  id: string | number;
  name: string;
  [key: string]: any;
}

interface ComboboxProps {
  label?: string;
  options: Option[];
  value: Option | null;
  onChange: (value: Option) => void;
  placeholder?: string;
  name?: string;
}

const CustomCombobox: React.FC<ComboboxProps> = ({ label, options, value, onChange, placeholder = 'ابحث واختر...', name }) => {
  const [query, setQuery] = useState('');

  const filteredOptions =
    query === ''
      ? options
      : options.filter((option) =>
          option.name
            .toLowerCase()
            .replace(/\s+/g, '')
            .includes(query.toLowerCase().replace(/\s+/g, ''))
        );

  return (
    <div className="w-full flex flex-col gap-2 font-display" dir="rtl">
      {label && (
        <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">
          {label}
        </label>
      )}

      <Combobox value={value} onChange={onChange} name={name}>
        <div className="relative mt-1">
          <div className="relative w-full cursor-default overflow-hidden rounded-2xl bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 shadow-sm focus-within:ring-4 focus-within:ring-blue-500/10 focus-within:border-blue-500 transition-all duration-300">
            <Search className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Combobox.Input
              className="w-full h-14 bg-transparent py-3 pr-12 pl-12 text-right text-slate-900 dark:text-white font-bold focus:outline-none placeholder:text-slate-400 dark:placeholder:text-slate-600"
              displayValue={(option: Option) => (option ? option.name : '')}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={placeholder}
            />
            <Combobox.Button className="absolute inset-y-0 left-0 flex items-center pl-4 group">
              <ChevronDown
                className="h-5 w-5 text-slate-400 group-hover:text-blue-500 transition-colors"
                aria-hidden="true"
              />
            </Combobox.Button>
          </div>

          <Transition
            as={Fragment}
            leave="transition ease-in duration-100"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
            afterLeave={() => setQuery('')}
          >
            <Combobox.Options className="absolute z-[100] mt-2 max-h-60 w-full overflow-auto rounded-2xl bg-white dark:bg-[#0B1120] py-2 text-right shadow-2xl border border-slate-100 dark:border-white/10 backdrop-blur-xl focus:outline-none scrollbar-hide">
              {filteredOptions.length === 0 && query !== '' ? (
                <div className="relative cursor-default select-none py-4 px-4 text-slate-400 text-center font-bold">
                  لا توجد نتائج مطابقة
                </div>
              ) : (
                filteredOptions.map((option) => (
                  <Combobox.Option
                    key={option.id}
                    className={({ active }) =>
                      `relative cursor-pointer select-none py-3.5 pr-4 pl-12 transition-all duration-200 ${
                        active 
                          ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400' 
                          : 'text-slate-700 dark:text-slate-200'
                      }`
                    }
                    value={option}
                  >
                    {({ selected }) => (
                      <>
                        <span
                          className={`block truncate font-display font-medium ${
                            selected ? 'font-bold text-blue-600 dark:text-blue-400' : ''
                          }`}
                        >
                          {option.name}
                        </span>
                        {selected ? (
                          <span className="absolute inset-y-0 left-4 flex items-center text-blue-600 dark:text-blue-400">
                            <Check className="h-4 w-4" aria-hidden="true" />
                          </span>
                        ) : null}
                      </>
                    )}
                  </Combobox.Option>
                ))
              )}
            </Combobox.Options>
          </Transition>
        </div>
      </Combobox>
    </div>
  );
};

export default CustomCombobox;
