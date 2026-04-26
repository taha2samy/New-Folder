import React, { Fragment } from 'react';
import { Listbox, Transition } from '@headlessui/react';
import { Check, ChevronDown } from 'lucide-react';

interface Option {
  id: string | number;
  name: string;
  [key: string]: any;
}

interface SelectProps {
  label?: string;
  options: Option[];
  value: Option | null;
  onChange: (value: Option) => void;
  placeholder?: string;
  name?: string;
}

const Select: React.FC<SelectProps> = ({ label, options, value, onChange, placeholder = 'اختر من القائمة...', name }) => {
  return (
    <div className="w-full flex flex-col gap-2 font-display" dir="rtl">
      {label && (
        <label className="text-xs font-black text-slate-400 uppercase tracking-widest px-1">
          {label}
        </label>
      )}
      
      <Listbox value={value} onChange={onChange} name={name}>
        <div className="relative mt-1">
          <Listbox.Button className="relative w-full cursor-pointer h-14 rounded-2xl bg-white dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 py-3 pr-12 pl-4 text-right shadow-sm focus:outline-none focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all duration-300">
            <span className="block truncate text-slate-900 dark:text-white font-bold">
              {value ? value.name : <span className="text-slate-400 dark:text-slate-600 font-medium">{placeholder}</span>}
            </span>
            <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-4">
              <ChevronDown className="h-5 w-5 text-slate-400 group-hover:text-blue-500 transition-colors" aria-hidden="true" />
            </span>
          </Listbox.Button>

          <Transition
            as={Fragment}
            leave="transition ease-in duration-100"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <Listbox.Options className="absolute z-[100] mt-2 max-h-60 w-full overflow-auto rounded-2xl bg-white dark:bg-[#0B1120] py-2 text-right shadow-2xl border border-slate-100 dark:border-white/10 backdrop-blur-xl focus:outline-none scrollbar-hide">
              {options.length === 0 ? (
                <div className="relative cursor-default select-none py-4 px-4 text-slate-400 text-center font-bold">
                  لا توجد خيارات متاحة
                </div>
              ) : (
                options.map((option) => (
                  <Listbox.Option
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
                        <span className={`block truncate font-display font-medium ${selected ? 'font-bold text-blue-600 dark:text-blue-400' : ''}`}>
                          {option.name}
                        </span>
                        {selected ? (
                          <span className="absolute inset-y-0 left-4 flex items-center text-blue-600 dark:text-blue-400">
                            <Check className="h-4 w-4" aria-hidden="true" />
                          </span>
                        ) : null}
                      </>
                    )}
                  </Listbox.Option>
                ))
              )}
            </Listbox.Options>
          </Transition>
        </div>
      </Listbox>
    </div>
  );
};

export default Select;
