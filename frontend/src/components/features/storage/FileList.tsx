import { useState } from 'react'
import {
  DocumentIcon,
  FolderIcon,
  TrashIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline'
import { formatDistanceToNow } from 'date-fns'

interface FileItem {
  name: string
  size: number
  lastModified: string
  type: 'file' | 'folder'
}

interface FileListProps {
  files: FileItem[]
  onDownload: (file: FileItem) => void
  onDelete: (file: FileItem) => void
  onNavigate: (file: FileItem) => void
}

export default function FileList({
  files,
  onDownload,
  onDelete,
  onNavigate,
}: FileListProps) {
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null)

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="mt-8 flow-root">
      <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
        <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
          <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
            <table className="min-w-full divide-y divide-gray-300">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">
                    Name
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                    Size
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                    Last Modified
                  </th>
                  <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {files.map((file) => (
                  <tr
                    key={file.name}
                    className={`${
                      selectedFile?.name === file.name ? 'bg-gray-50' : ''
                    } hover:bg-gray-50`}
                    onClick={() => setSelectedFile(file)}
                  >
                    <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm sm:pl-6">
                      <div className="flex items-center">
                        {file.type === 'folder' ? (
                          <FolderIcon className="h-5 w-5 flex-shrink-0 text-gray-400" />
                        ) : (
                          <DocumentIcon className="h-5 w-5 flex-shrink-0 text-gray-400" />
                        )}
                        <div className="ml-4">
                          <button
                            className="font-medium text-gray-900 hover:text-primary-600"
                            onClick={() => onNavigate(file)}
                          >
                            {file.name}
                          </button>
                        </div>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {file.type === 'file' ? formatFileSize(file.size) : '--'}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {formatDistanceToNow(new Date(file.lastModified), { addSuffix: true })}
                    </td>
                    <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                      <div className="flex justify-end gap-2">
                        {file.type === 'file' && (
                          <button
                            onClick={() => onDownload(file)}
                            className="text-primary-600 hover:text-primary-900"
                          >
                            <ArrowDownTrayIcon className="h-5 w-5" />
                          </button>
                        )}
                        <button
                          onClick={() => onDelete(file)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}