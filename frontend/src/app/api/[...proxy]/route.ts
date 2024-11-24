import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const path = request.nextUrl.pathname.replace('/api/', '');
    const searchParams = request.nextUrl.searchParams.toString();
    const url = `${API_URL}/api/v1/${path}${searchParams ? `?${searchParams}` : ''}`;

    console.log('Proxy GET request to:', url);

    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('Authorization')
          ? { Authorization: request.headers.get('Authorization')! }
          : {}),
      },
    });

    const data = await response.json();
    console.log('Proxy GET response:', data);

    return NextResponse.json(data);
  } catch (error) {
    console.error('API proxy GET error:', error);
    return NextResponse.json(
      { error: 'Internal Server Error', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const path = request.nextUrl.pathname.replace('/api/', '');
    const url = `${API_URL}/api/v1/${path}`;
    
    // Clone the request to read the body
    const clonedRequest = request.clone();
    const body = await clonedRequest.json();
    
    console.log('Proxy POST request:', {
      url,
      body,
      headers: Object.fromEntries(request.headers),
    });

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('Authorization')
          ? { Authorization: request.headers.get('Authorization')! }
          : {}),
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Proxy POST error response:', {
        status: response.status,
        statusText: response.statusText,
        body: errorText,
      });
      return NextResponse.json(
        { error: 'Backend Error', details: errorText },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('Proxy POST response:', data);

    return NextResponse.json(data);
  } catch (error) {
    console.error('API proxy POST error:', error);
    return NextResponse.json(
      { error: 'Internal Server Error', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const path = request.nextUrl.pathname.replace('/api/', '');
    const url = `${API_URL}/api/v1/${path}`;

    console.log('Proxy DELETE request to:', url);

    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...(request.headers.get('Authorization')
          ? { Authorization: request.headers.get('Authorization')! }
          : {}),
      },
    });

    if (response.status === 204) {
      return new NextResponse(null, { status: 204 });
    }

    const data = await response.json();
    console.log('Proxy DELETE response:', data);
    return NextResponse.json(data);
  } catch (error) {
    console.error('API proxy DELETE error:', error);
    return NextResponse.json(
      { error: 'Internal Server Error', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
